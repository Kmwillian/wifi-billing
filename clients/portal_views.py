from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from packages.models import Package
from .models import Client, Session
from .forms import PortalConnectForm


class CaptivePortalView(View):
    """
    This is the page clients see when they connect to WiFi
    and get redirected before they can browse the internet.
    """
    template_name = 'portal/home.html'

    def get(self, request):
        packages = Package.objects.filter(status='active').order_by('sort_order', 'price')
        # Check if client already has an active session by MAC
        mac = request.GET.get('mac', '')
        ip = request.GET.get('ip', '')
        existing_client = None
        active_session = None

        if mac:
            existing_client = Client.objects.filter(mac_address=mac).first()
            if existing_client:
                active_session = existing_client.active_session

        context = {
            'packages': packages,
            'mac': mac,
            'ip': ip,
            'existing_client': existing_client,
            'active_session': active_session,
        }
        return render(request, self.template_name, context)


class InitiatePaymentView(View):
    """Handles the STK Push initiation from captive portal"""
    template_name = 'portal/home.html'

    def post(self, request):
        form = PortalConnectForm(request.POST)
        if not form.is_valid():
            packages = Package.objects.filter(status='active')
            return render(request, self.template_name, {
                'packages': packages,
                'errors': form.errors
            })

        phone = form.cleaned_data['phone']
        package_id = form.cleaned_data['package_id']
        package = get_object_or_404(Package, pk=package_id, status='active')

        # Normalize phone number to 254XXXXXXXXX
        phone = phone.strip().replace(' ', '')
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('+'):
            phone = phone[1:]

        # Get or create client by phone
        client, created = Client.objects.get_or_create(
            phone=phone,
            defaults={
                'full_name': f'Client {phone}',
                'mikrotik_username': f'user_{phone}',
            }
        )

        # Store in session for callback to reference
        request.session['portal_phone'] = phone
        request.session['portal_package_id'] = package_id
        request.session['portal_client_id'] = client.pk

        # Import here to avoid circular imports
        from payments.mpesa import initiate_stk_push
        from payments.models import Payment

        # Create pending payment record
        payment = Payment.objects.create(
            client=client,
            package=package,
            amount=package.price,
            phone=phone,
            status='pending',
        )

        # Initiate STK push
        success, response = initiate_stk_push(
            phone=phone,
            amount=int(package.price),
            account_reference=f'WIFI-{client.pk}',
            description=f'{package.name} WiFi Package',
            payment_id=payment.pk,
        )

        if success:
            payment.checkout_request_id = response.get('CheckoutRequestID', '')
            payment.merchant_request_id = response.get('MerchantRequestID', '')
            payment.save()
            return redirect('portal_status')
        else:
            payment.status = 'failed'
            payment.save()
            packages = Package.objects.filter(status='active')
            return render(request, self.template_name, {
                'packages': packages,
                'error': 'Could not initiate payment. Please try again.',
            })


class ConnectionStatusView(View):
    """Polling page — client waits here while payment processes"""
    template_name = 'portal/status.html'

    def get(self, request):
        client_id = request.session.get('portal_client_id')
        package_id = request.session.get('portal_package_id')

        if not client_id:
            return redirect('portal_home')

        client = get_object_or_404(Client, pk=client_id)
        package = get_object_or_404(Package, pk=package_id)

        return render(request, 'portal/status.html', {
            'client': client,
            'package': package,
        })


class PaymentSuccessView(View):
    template_name = 'portal/success.html'

    def get(self, request):
        client_id = request.session.get('portal_client_id')
        if not client_id:
            return redirect('portal_home')
        client = get_object_or_404(Client, pk=client_id)
        active_session = client.active_session
        return render(request, 'portal/success.html', {
            'client': client,
            'session': active_session,
        })