from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Payment, ManualActivation


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'client', 'package', 'amount_display',
        'phone', 'payment_method', 'status_badge',
        'mpesa_receipt_number', 'initiated_at'
    ]
    list_filter = ['status', 'payment_method', 'initiated_at']
    search_fields = [
        'client__full_name', 'client__phone',
        'phone', 'mpesa_receipt_number',
        'checkout_request_id'
    ]
    readonly_fields = [
        'checkout_request_id', 'merchant_request_id',
        'mpesa_receipt_number', 'mpesa_transaction_date',
        'raw_callback', 'initiated_at', 'completed_at',
        'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Payment Info', {
            'fields': (
                'client', 'package', 'session',
                'amount', 'phone', 'payment_method', 'status'
            )
        }),
        ('M-Pesa Details', {
            'fields': (
                'checkout_request_id', 'merchant_request_id',
                'mpesa_receipt_number', 'mpesa_transaction_date'
            )
        }),
        ('Timestamps', {
            'fields': ('initiated_at', 'completed_at', 'created_at', 'updated_at'),
        }),
        ('Raw Callback Data', {
            'fields': ('raw_callback',),
            'classes': ('collapse',),
        }),
    )

    def amount_display(self, obj):
        return format_html('<strong>KES {}</strong>', obj.amount)
    amount_display.short_description = 'Amount'

    def status_badge(self, obj):
        colors = {
            'completed': '#16a34a',
            'pending': '#f59e0b',
            'failed': '#dc2626',
            'cancelled': '#6b7280',
            'refunded': '#7c3aed',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;'
            'border-radius:12px;font-size:12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ManualActivation)
class ManualActivationAdmin(admin.ModelAdmin):
    list_display = [
        'client', 'package', 'activated_by',
        'activated_at', 'notes'
    ]
    list_filter = ['activated_at', 'package']
    search_fields = ['client__full_name', 'client__phone', 'activated_by__username']
    readonly_fields = ['activated_at']