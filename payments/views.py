import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta
from .models import Payment, ManualActivation
from .forms import ManualActivationForm
from .mpesa import initiate_stk_push, query_stk_status
from .session_activator import activate_session_after_payment
from clients.models import Client
from accounts.decorators import admin_required

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class PaymentListView(View):
    template_name = 'payments/payment_list.html'

    def get(self, request):
        payments = Payment.objects.select_related(
            'client', 'package'
        ).all().order_by('-created_at')

        # Filters
        status = request.GET.get('status', '')
        method = request.GET.get('method', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        if status:
            payments = payments.filter(status=status)
        if method:
            payments = payments.filter(payment_method=method)
        if date_from:
            payments = payments.filter(created_at__date__gte=date_from)
        if date_to:
            payments = payments.filter(created_at__date__lte=date_to)

        # Summary stats
        today = timezone.now().date()
        today_revenue = Payment.objects.filter(
            status='completed',
            completed_at__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0

        month_revenue = Payment.objects.filter(
            status='completed',
            completed_at__month=today.month,
            completed_at__year=today.year,
        ).aggregate(total=Sum('amount'))['total'] or 0

        context = {
            'payments': payments[:100],
            'today_revenue': today_revenue,
            'month_revenue': month_revenue,
            'total_count': payments.count(),
            'completed_count': payments.filter(status='completed').count(),
            'pending_count': payments.filter(status='pending').count(),
            'failed_count': payments.filter(status='failed').count(),
            'status_filter': status,
            'method_filter': method,
        }
        return render(request, self.template_name, context)


@method_decorator([login_required, admin_required], name='dispatch')
class ManualActivationView(View):
    template_name = 'payments/manual_activation.html'

    def get(self, request):
        form = ManualActivationForm()
        recent = ManualActivation.objects.select_related(
            'client', 'package', 'activated_by'
        ).all()[:10]
        return render(request, self.template_name, {'form': form, 'recent': recent})

    def post(self, request):
        form = ManualActivationForm(request.POST)
        if not form.is_valid():
            recent = ManualActivation.objects.all()[:10]
            return render(request, self.template_name, {'form': form, 'recent': recent})

        phone = form.cleaned_data['client_phone']
        package = form.cleaned_data['package']
        amount = form.cleaned_data['amount_paid']
        notes = form.cleaned_data['notes']

        # Get or create client
        client, created = Client.objects.get_or_create(
            phone=phone,
            defaults={
                'full_name': f'Client {phone}',
                'mikrotik_username': f'user_{phone}',
            }
        )

        # Create payment record
        payment = Payment.objects.create(
            client=client,
            package=package,
            amount=amount,
            phone=phone,
            payment_method='cash',
            status='pending',
        )

        # Activate session
        try:
            session = activate_session_after_payment(payment)
            ManualActivation.objects.create(
                client=client,
                package=package,
                activated_by=request.user,
                payment=payment,
                notes=notes,
            )
            messages.success(
                request,
                f'Session activated for {client.full_name} | '
                f'{package.name} | Expires: {session.expires_at.strftime("%H:%M %d %b")}'
            )
        except Exception as e:
            payment.status = 'failed'
            payment.save()
            messages.error(request, f'Activation failed: {str(e)}')

        return redirect('payments:manual_activation')


@csrf_exempt
def mpesa_callback(request):
    """
    Safaricom calls this URL after STK Push.
    CSRF exempt because Safaricom does not send CSRF token.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        body = json.loads(request.body)
        logger.info(f"M-Pesa Callback received: {body}")

        stk_callback = body.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        checkout_request_id = stk_callback.get('CheckoutRequestID', '')

        # Find the payment by CheckoutRequestID
        try:
            payment = Payment.objects.get(checkout_request_id=checkout_request_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for CheckoutRequestID: {checkout_request_id}")
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})

        # Save raw callback
        payment.raw_callback = body

        if result_code == 0:
            # Payment successful
            callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            metadata = {item['Name']: item.get('Value') for item in callback_metadata}

            payment.mpesa_receipt_number = metadata.get('MpesaReceiptNumber', '')
            payment.mpesa_transaction_date = str(metadata.get('TransactionDate', ''))
            payment.save()

            # Activate the session
            try:
                activate_session_after_payment(payment)
                logger.info(
                    f"Session activated via M-Pesa callback | "
                    f"Receipt: {payment.mpesa_receipt_number}"
                )
            except Exception as e:
                logger.error(f"Session activation failed after payment: {e}")

        else:
            # Payment failed or cancelled
            result_desc = stk_callback.get('ResultDesc', 'Unknown error')
            payment.status = 'failed'
            payment.save()
            logger.warning(
                f"M-Pesa payment failed | "
                f"Code: {result_code} | "
                f"Desc: {result_desc}"
            )

        # Always return success to Safaricom
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})

    except Exception as e:
        logger.error(f"M-Pesa callback processing error: {e}")
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})


@login_required
def check_payment_status(request, payment_id):
    """
    AJAX endpoint polled by portal status page
    to check if payment has been completed
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    data = {
        'status': payment.status,
        'is_completed': payment.is_completed,
        'receipt': payment.mpesa_receipt_number,
    }

    if payment.is_pending:
        # Also query M-Pesa directly as fallback
        if payment.checkout_request_id:
            success, response = query_stk_status(payment.checkout_request_id)
            if success and response.get('ResultCode') == '0':
                data['mpesa_status'] = 'completed'
            else:
                data['mpesa_status'] = 'pending'

    return JsonResponse(data)


@login_required
def payment_detail_view(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related('client', 'package', 'session'),
        pk=pk
    )
    return render(request, 'payments/payment_detail.html', {'payment': payment})


@login_required
def revenue_chart_api(request):
    """
    Returns last 7 days revenue data for Chart.js
    """
    today = timezone.now().date()
    labels = []
    data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        revenue = Payment.objects.filter(
            status='completed',
            completed_at__date=day
        ).aggregate(total=Sum('amount'))['total'] or 0
        labels.append(day.strftime('%a %d'))
        data.append(float(revenue))

    return JsonResponse({'labels': labels, 'data': data})