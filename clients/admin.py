from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Client, Session


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'phone', 'email',
        'mikrotik_username', 'status_badge',
        'active_session_display', 'total_sessions',
        'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['full_name', 'phone', 'email', 'mac_address', 'mikrotik_username']
    readonly_fields = ['mikrotik_username', 'mikrotik_password', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Personal Info', {
            'fields': ('full_name', 'phone', 'email', 'id_number', 'notes')
        }),
        ('Network Info', {
            'fields': ('mac_address', 'ip_address', 'mikrotik_username', 'mikrotik_password')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'active': '#16a34a',
            'inactive': '#6b7280',
            'blocked': '#dc2626',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;'
            'border-radius:12px;font-size:12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def active_session_display(self, obj):
        session = obj.active_session
        if session:
            return format_html(
                '<span style="color:#16a34a;font-weight:bold;">● {}</span>',
                session.time_remaining_display
            )
        return format_html('<span style="color:#9ca3af;">No active session</span>')
    active_session_display.short_description = 'Active Session'


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = [
        'client', 'package', 'status_badge',
        'started_at', 'expires_at',
        'time_remaining_display', 'data_used_display'
    ]
    list_filter = ['status', 'started_at', 'package']
    search_fields = ['client__full_name', 'client__phone', 'ip_address', 'mac_address']
    readonly_fields = [
        'started_at', 'created_at', 'mikrotik_session_id',
        'data_used_mb', 'upload_bytes', 'download_bytes'
    ]
    ordering = ['-started_at']

    def status_badge(self, obj):
        colors = {
            'active': '#16a34a',
            'expired': '#f59e0b',
            'terminated': '#dc2626',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;'
            'border-radius:12px;font-size:12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def time_remaining_display(self, obj):
        return obj.time_remaining_display
    time_remaining_display.short_description = 'Time Remaining'

    def data_used_display(self, obj):
        return obj.data_used_display
    data_used_display.short_description = 'Data Used'