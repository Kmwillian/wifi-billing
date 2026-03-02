from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate, TruncMonth
from django.http import JsonResponse
from datetime import timedelta, date
from clients.models import Client, Session
from packages.models import Package
from payments.models import Payment
from accounts.models import AuditLog


@method_decorator(login_required, name='dispatch')
class DashboardHomeView(View):
    template_name = 'dashboard/home.html'

    def get(self, request):
        today = timezone.now().date()
        now = timezone.now()

        # ── Active sessions ──────────────────────────────
        active_sessions = Session.objects.filter(status='active').count()

        # ── Today stats ──────────────────────────────────
        today_revenue = Payment.objects.filter(
            status='completed',
            completed_at__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0

        today_payments = Payment.objects.filter(
            status='completed',
            completed_at__date=today
        ).count()

        today_new_clients = Client.objects.filter(
            created_at__date=today
        ).count()

        # ── Month stats ───────────────────────────────────
        month_revenue = Payment.objects.filter(
            status='completed',
            completed_at__month=today.month,
            completed_at__year=today.year,
        ).aggregate(total=Sum('amount'))['total'] or 0

        month_payments = Payment.objects.filter(
            status='completed',
            completed_at__month=today.month,
            completed_at__year=today.year,
        ).count()

        # ── Total stats ───────────────────────────────────
        total_clients = Client.objects.count()
        total_revenue = Payment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0

        # ── Yesterday comparison for % change ────────────
        yesterday = today - timedelta(days=1)
        yesterday_revenue = Payment.objects.filter(
            status='completed',
            completed_at__date=yesterday
        ).aggregate(total=Sum('amount'))['total'] or 0

        if yesterday_revenue > 0:
            revenue_change = ((today_revenue - yesterday_revenue) / yesterday_revenue) * 100
        else:
            revenue_change = 100 if today_revenue > 0 else 0

        # ── Top packages this month ───────────────────────
        top_packages = Package.objects.filter(
            payments__status='completed',
            payments__completed_at__month=today.month,
            payments__completed_at__year=today.year,
        ).annotate(
            sales_count=Count('payments'),
            sales_revenue=Sum('payments__amount')
        ).order_by('-sales_count')[:5]

        # ── Recent payments ───────────────────────────────
        recent_payments = Payment.objects.filter(
            status='completed'
        ).select_related('client', 'package').order_by('-completed_at')[:10]

        # ── Recent sessions ───────────────────────────────
        recent_sessions = Session.objects.filter(
            status='active'
        ).select_related('client', 'package').order_by('-started_at')[:8]

        # ── Pending payments ──────────────────────────────
        pending_payments = Payment.objects.filter(
            status='pending'
        ).count()

        # ── Last 7 days revenue for sparkline ─────────────
        last_7_days = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            rev = Payment.objects.filter(
                status='completed',
                completed_at__date=day
            ).aggregate(total=Sum('amount'))['total'] or 0
            last_7_days.append({'day': day.strftime('%a'), 'revenue': float(rev)})

        # ── Recent audit logs ─────────────────────────────
        recent_logs = AuditLog.objects.select_related('user').all()[:5]

        context = {
            # Cards
            'active_sessions': active_sessions,
            'today_revenue': today_revenue,
            'today_payments': today_payments,
            'today_new_clients': today_new_clients,
            'month_revenue': month_revenue,
            'month_payments': month_payments,
            'total_clients': total_clients,
            'total_revenue': total_revenue,
            'revenue_change': round(revenue_change, 1),
            'pending_payments': pending_payments,

            # Lists
            'top_packages': top_packages,
            'recent_payments': recent_payments,
            'recent_sessions': recent_sessions,
            'recent_logs': recent_logs,
            'last_7_days': last_7_days,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class AnalyticsView(View):
    template_name = 'dashboard/analytics.html'

    def get(self, request):
        today = timezone.now().date()

        # ── Last 30 days daily revenue ────────────────────
        daily_revenue = []
        daily_labels = []
        for i in range(29, -1, -1):
            day = today - timedelta(days=i)
            rev = Payment.objects.filter(
                status='completed',
                completed_at__date=day
            ).aggregate(total=Sum('amount'))['total'] or 0
            daily_labels.append(day.strftime('%d %b'))
            daily_revenue.append(float(rev))

        # ── Monthly revenue last 6 months ─────────────────
        monthly_labels = []
        monthly_revenue = []
        for i in range(5, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=i * 30)
            rev = Payment.objects.filter(
                status='completed',
                completed_at__month=month_date.month,
                completed_at__year=month_date.year,
            ).aggregate(total=Sum('amount'))['total'] or 0
            monthly_labels.append(month_date.strftime('%b %Y'))
            monthly_revenue.append(float(rev))

        # ── Package distribution ──────────────────────────
        package_stats = Package.objects.filter(
            payments__status='completed'
        ).annotate(
            sales=Count('payments')
        ).order_by('-sales')[:6]

        package_labels = [p.name for p in package_stats]
        package_data = [p.sales for p in package_stats]

        # ── Payment method breakdown ──────────────────────
        mpesa_count = Payment.objects.filter(
            status='completed', payment_method='mpesa'
        ).count()
        cash_count = Payment.objects.filter(
            status='completed', payment_method='cash'
        ).count()
        manual_count = Payment.objects.filter(
            status='completed', payment_method='manual'
        ).count()

        # ── Client growth last 30 days ────────────────────
        client_growth_labels = []
        client_growth_data = []
        for i in range(29, -1, -1):
            day = today - timedelta(days=i)
            count = Client.objects.filter(
                created_at__date__lte=day
            ).count()
            client_growth_labels.append(day.strftime('%d %b'))
            client_growth_data.append(count)

        # ── Session stats ─────────────────────────────────
        total_sessions = Session.objects.count()
        active_sessions = Session.objects.filter(status='active').count()
        expired_sessions = Session.objects.filter(status='expired').count()
        terminated_sessions = Session.objects.filter(status='terminated').count()

        context = {
            'daily_labels': daily_labels,
            'daily_revenue': daily_revenue,
            'monthly_labels': monthly_labels,
            'monthly_revenue': monthly_revenue,
            'package_labels': package_labels,
            'package_data': package_data,
            'mpesa_count': mpesa_count,
            'cash_count': cash_count,
            'manual_count': manual_count,
            'client_growth_labels': client_growth_labels,
            'client_growth_data': client_growth_data,
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'expired_sessions': expired_sessions,
            'terminated_sessions': terminated_sessions,
        }
        return render(request, self.template_name, context)


@login_required
def live_stats_api(request):
    """
    AJAX endpoint polled every 30 seconds by dashboard
    to update live stats without page refresh
    """
    today = timezone.now().date()

    active_sessions = Session.objects.filter(status='active').count()

    today_revenue = Payment.objects.filter(
        status='completed',
        completed_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or 0

    pending_payments = Payment.objects.filter(status='pending').count()

    recent_payment = Payment.objects.filter(
        status='completed'
    ).select_related('client', 'package').first()

    recent_data = None
    if recent_payment:
        recent_data = {
            'client': recent_payment.client.full_name if recent_payment.client else 'Unknown',
            'package': recent_payment.package.name if recent_payment.package else 'Unknown',
            'amount': float(recent_payment.amount),
            'receipt': recent_payment.mpesa_receipt_number,
            'time': recent_payment.completed_at.strftime('%H:%M') if recent_payment.completed_at else '',
        }

    return JsonResponse({
        'active_sessions': active_sessions,
        'today_revenue': float(today_revenue),
        'pending_payments': pending_payments,
        'recent_payment': recent_data,
        'timestamp': timezone.now().strftime('%H:%M:%S'),
    })