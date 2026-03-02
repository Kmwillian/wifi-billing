from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def admin_required(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_admin:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard:home')
        return func(request, *args, **kwargs)
    return wrapper


def superadmin_required(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_superadmin:
            messages.error(request, 'Only Super Admins can access this page.')
            return redirect('dashboard:home')
        return func(request, *args, **kwargs)
    return wrapper