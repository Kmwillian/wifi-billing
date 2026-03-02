from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from .models import Client, Session
from .forms import ClientForm
from .mikrotik import disconnect_active_session, remove_hotspot_user
from accounts.decorators import admin_required


@method_decorator(login_required, name='dispatch')
class ClientListView(View):
    template_name = 'clients/client_list.html'

    def get(self, request):
        clients = Client.objects.prefetch_related('sessions').all()
        status_filter = request.GET.get('status', '')
        search = request.GET.get('search', '')

        if status_filter:
            clients = clients.filter(status=status_filter)
        if search:
            clients = clients.filter(
                full_name__icontains=search
            ) | clients.filter(
                phone__icontains=search
            ) | clients.filter(
                mac_address__icontains=search
            )

        context = {
            'clients': clients,
            'active_count': Client.objects.filter(status='active').count(),
            'inactive_count': Client.objects.filter(status='inactive').count(),
            'blocked_count': Client.objects.filter(status='blocked').count(),
            'status_filter': status_filter,
            'search': search,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class ClientDetailView(View):
    template_name = 'clients/client_detail.html'

    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        sessions = client.sessions.select_related('package').all()[:20]
        context = {
            'client': client,
            'sessions': sessions,
            'active_session': client.active_session,
        }
        return render(request, self.template_name, context)


@method_decorator([login_required, admin_required], name='dispatch')
class ClientCreateView(View):
    template_name = 'clients/client_form.html'

    def get(self, request):
        form = ClientForm()
        return render(request, self.template_name, {'form': form, 'title': 'Add New Client'})

    def post(self, request):
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Client {client.full_name} added successfully.')
            return redirect('clients:detail', pk=client.pk)
        return render(request, self.template_name, {'form': form, 'title': 'Add New Client'})


@method_decorator([login_required, admin_required], name='dispatch')
class ClientUpdateView(View):
    template_name = 'clients/client_form.html'

    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        form = ClientForm(instance=client)
        return render(request, self.template_name, {
            'form': form,
            'title': f'Edit Client — {client.full_name}',
            'client': client
        })

    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client updated successfully.')
            return redirect('clients:detail', pk=client.pk)
        return render(request, self.template_name, {
            'form': form,
            'title': f'Edit Client — {client.full_name}',
            'client': client
        })


@login_required
@admin_required
def client_block_view(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if client.status == 'blocked':
        client.status = 'inactive'
        messages.success(request, f'{client.full_name} has been unblocked.')
    else:
        # Terminate active sessions first
        active_session = client.active_session
        if active_session:
            disconnect_active_session(client.mikrotik_username)
            active_session.terminate('blocked')
        client.status = 'blocked'
        messages.warning(request, f'{client.full_name} has been blocked.')
    client.save()
    return redirect('clients:detail', pk=pk)


@login_required
def terminate_session_view(request, session_id):
    session = get_object_or_404(Session, pk=session_id)
    disconnect_active_session(session.client.mikrotik_username)
    session.terminate('admin_manual')
    session.client.status = 'inactive'
    session.client.save()
    messages.success(request, 'Session terminated successfully.')
    return redirect('clients:detail', pk=session.client.pk)


@login_required
def active_sessions_view(request):
    sessions = Session.objects.filter(
        status='active'
    ).select_related('client', 'package').order_by('-started_at')
    return render(request, 'clients/active_sessions.html', {'sessions': sessions})


@login_required
def session_stats_api(request):
    """AJAX endpoint for live session stats on dashboard"""
    active = Session.objects.filter(status='active').count()
    expired_today = Session.objects.filter(
        status='expired',
        ended_at__date=timezone.now().date()
    ).count()
    return JsonResponse({
        'active_sessions': active,
        'expired_today': expired_today,
    })