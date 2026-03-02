from django.contrib import admin
from django.utils.html import format_html
from .models import Package


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'price_display', 'duration_display',
        'data_limit_display', 'speed_display',
        'max_devices', 'status_badge', 'is_featured', 'sort_order'
    ]
    list_filter = ['status', 'duration_unit', 'is_featured']
    search_fields = ['name', 'description', 'mikrotik_profile']
    list_editable = ['sort_order', 'is_featured']
    ordering = ['sort_order', 'price']

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'price', 'status', 'is_featured', 'sort_order')
        }),
        ('Duration', {
            'fields': ('duration', 'duration_unit')
        }),
        ('Limits', {
            'fields': ('data_limit_mb', 'upload_speed_kbps', 'download_speed_kbps', 'max_devices'),
            'description': 'Leave speed/data fields blank for unlimited access.'
        }),
        ('MikroTik', {
            'fields': ('mikrotik_profile',),
            'description': 'Must match the hotspot profile name on your MikroTik router.'
        }),
    )

    def price_display(self, obj):
        return format_html('<strong>KES {}</strong>', obj.price)
    price_display.short_description = 'Price'

    def status_badge(self, obj):
        if obj.status == 'active':
            return format_html(
                '<span style="background:#16a34a;color:white;padding:3px 10px;border-radius:12px;font-size:12px;">Active</span>'
            )
        return format_html(
            '<span style="background:#dc2626;color:white;padding:3px 10px;border-radius:12px;font-size:12px;">Inactive</span>'
        )
    status_badge.short_description = 'Status'

    def duration_display(self, obj):
        return obj.duration_display
    duration_display.short_description = 'Duration'

    def data_limit_display(self, obj):
        return obj.data_limit_display
    data_limit_display.short_description = 'Data Limit'

    def speed_display(self, obj):
        return obj.speed_display
    speed_display.short_description = 'Speed'