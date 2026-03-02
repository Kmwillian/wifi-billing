from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AuditLog


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'get_full_name', 'email', 'phone', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone']
    ordering = ['-created_at']

    fieldsets = UserAdmin.fieldsets + (
        ('Staff Info', {
            'fields': ('role', 'phone', 'profile_photo')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Staff Info', {
            'fields': ('role', 'phone', 'email', 'first_name', 'last_name')
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'target', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__username', 'target', 'detail']
    readonly_fields = ['user', 'action', 'target', 'detail', 'ip_address', 'timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False