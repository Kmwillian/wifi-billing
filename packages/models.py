from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Package(models.Model):
    DURATION_UNIT_CHOICES = [
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))]
    )
    duration = models.PositiveIntegerField(help_text='Duration value e.g. 1, 6, 24')
    duration_unit = models.CharField(max_length=10, choices=DURATION_UNIT_CHOICES, default='hours')
    
    # Data limits
    data_limit_mb = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Data limit in MB. Leave blank for unlimited.'
    )
    
    # Speed limits
    upload_speed_kbps = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Upload speed limit in Kbps. Leave blank for unlimited.'
    )
    download_speed_kbps = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Download speed limit in Kbps. Leave blank for unlimited.'
    )

    # Device limit
    max_devices = models.PositiveIntegerField(default=1)

    # MikroTik profile name (must match exactly on router)
    mikrotik_profile = models.CharField(
        max_length=100,
        blank=True,
        help_text='MikroTik hotspot profile name e.g. "1hr-plan"'
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    is_featured = models.BooleanField(default=False, help_text='Show this plan prominently on portal')
    sort_order = models.PositiveIntegerField(default=0, help_text='Lower number shows first')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'price']
        verbose_name = 'Package'
        verbose_name_plural = 'Packages'

    def __str__(self):
        return f"{self.name} — KES {self.price}"

    @property
    def duration_display(self):
        unit = self.duration_unit.rstrip('s') if self.duration == 1 else self.duration_unit
        return f"{self.duration} {unit}"

    @property
    def data_limit_display(self):
        if not self.data_limit_mb:
            return 'Unlimited'
        if self.data_limit_mb >= 1024:
            return f"{self.data_limit_mb / 1024:.1f} GB"
        return f"{self.data_limit_mb} MB"

    @property
    def speed_display(self):
        if not self.download_speed_kbps:
            return 'Unlimited'
        if self.download_speed_kbps >= 1024:
            return f"{self.download_speed_kbps / 1024:.1f} Mbps"
        return f"{self.download_speed_kbps} Kbps"

    @property
    def duration_in_seconds(self):
        multipliers = {
            'minutes': 60,
            'hours': 3600,
            'days': 86400,
            'weeks': 604800,
            'months': 2592000,
        }
        return self.duration * multipliers.get(self.duration_unit, 3600)

    def is_active(self):
        return self.status == 'active'