from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from .models import User, AuditLog
from .forms import LoginForm, StaffCreateForm, StaffUpdateForm
from .decorators import admin_required


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            AuditLog.objects.create(
                user=user,
                action='login',
                target='System',
                detail=f'{user.username} logged in',
                ip_address=get_client_ip(request)
            )
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard:home')
        messages.error(request, 'Invalid username or password.')
        return render(request, self.template_name, {'form': form})


@login_required
def logout_view(request):
    AuditLog.objects.create(
        user=request.user,
        action='logout',
        target='System',
        detail=f'{request.user.username} logged out',
        ip_address=get_client_ip(request)
    )
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@method_decorator([login_required, admin_required], name='dispatch')
class StaffListView(View):
    template_name = 'accounts/staff_list.html'

    def get(self, request):
        staff = User.objects.all().order_by('-created_at')
        return render(request, self.template_name, {'staff': staff})


@method_decorator([login_required, admin_required], name='dispatch')
class StaffCreateView(View):
    template_name = 'accounts/staff_form.html'

    def get(self, request):
        form = StaffCreateForm()
        return render(request, self.template_name, {'form': form, 'title': 'Add Staff Member'})

    def post(self, request):
        form = StaffCreateForm(request.POST, request.FILES)
        if form.is_valid():
            staff = form.save()
            AuditLog.objects.create(
                user=request.user,
                action='create',
                target=f'Staff: {staff.username}',
                detail=f'Created staff account for {staff.get_full_name()}',
                ip_address=get_client_ip(request)
            )
            messages.success(request, f'Staff member {staff.get_full_name()} created successfully.')
            return redirect('accounts:staff_list')
        return render(request, self.template_name, {'form': form, 'title': 'Add Staff Member'})


@method_decorator([login_required, admin_required], name='dispatch')
class StaffUpdateView(View):
    template_name = 'accounts/staff_form.html'

    def get(self, request, pk):
        staff = get_object_or_404(User, pk=pk)
        form = StaffUpdateForm(instance=staff)
        return render(request, self.template_name, {'form': form, 'title': 'Edit Staff Member', 'staff': staff})

    def post(self, request, pk):
        staff = get_object_or_404(User, pk=pk)
        form = StaffUpdateForm(request.POST, request.FILES, instance=staff)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                user=request.user,
                action='update',
                target=f'Staff: {staff.username}',
                detail=f'Updated staff account for {staff.get_full_name()}',
                ip_address=get_client_ip(request)
            )
            messages.success(request, 'Staff member updated successfully.')
            return redirect('accounts:staff_list')
        return render(request, self.template_name, {'form': form, 'title': 'Edit Staff Member', 'staff': staff})


@login_required
@admin_required
def staff_delete_view(request, pk):
    staff = get_object_or_404(User, pk=pk)
    if staff == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('accounts:staff_list')
    name = staff.get_full_name()
    staff.delete()
    AuditLog.objects.create(
        user=request.user,
        action='delete',
        target=f'Staff: {name}',
        detail=f'Deleted staff account: {name}',
        ip_address=get_client_ip(request)
    )
    messages.success(request, f'Staff member {name} deleted.')
    return redirect('accounts:staff_list')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def audit_log_view(request):
    logs = AuditLog.objects.select_related('user').all()[:200]
    return render(request, 'accounts/audit_log.html', {'logs': logs})