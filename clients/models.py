from django.db import models
from django.utils import timezone
from packages.models import Package


class Client(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blocked', 'Blocked'),
    ]

    # Identity
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True)
    id_number = models.CharField(max_length=20, blank=True, help_text='National ID or student number')

    # Network
    mac_address = models.CharField(
        max_length=17,
        blank=True,
        help_text='Device MAC address e.g. AA:BB:CC:DD:EE:FF'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mikrotik_username = models.CharField(
        max_length=100,
        unique=True,
        help_text='Auto-generated username used on MikroTik'
    )
    mikrotik_password = models.CharField(max_length=100)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='inactive')
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return f"{self.full_name} ({self.phone})"

    def save(self, *args, **kwargs):
        # Auto-generate MikroTik username from phone if not set
        if not self.mikrotik_username:
            self.mikrotik_username = f"user_{self.phone}"
        if not self.mikrotik_password:
            import random
            import string
            self.mikrotik_password = ''.join(
                random.choices(string.ascii_letters + string.digits, k=10)
            )
        super().save(*args, **kwargs)

    @property
    def active_session(self):
        return self.sessions.filter(status='active').first()

    @property
    def total_sessions(self):
        return self.sessions.count()

    @property
    def total_spent(self):
        from payments.models import Payment
        total = Payment.objects.filter(
            client=self,
            status='completed'
        ).aggregate(
            total=models.Sum('amount')
        )['total']
        return total or 0


class Session(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='sessions')
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True, related_name='sessions')

    # Timing
    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)

    # Network info at time of session
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=17, blank=True)

    # Usage tracking
    data_used_mb = models.FloatField(default=0.0)
    upload_bytes = models.BigIntegerField(default=0)
    download_bytes = models.BigIntegerField(default=0)

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    mikrotik_session_id = models.CharField(max_length=100, blank=True)
    terminated_by = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'

    def __str__(self):
        return f"{self.client.full_name} — {self.package} [{self.status}]"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def time_remaining(self):
        if self.status != 'active':
            return None
        remaining = self.expires_at - timezone.now()
        if remaining.total_seconds() <= 0:
            return None
        return remaining

    @property
    def time_remaining_display(self):
        remaining = self.time_remaining
        if not remaining:
            return 'Expired'
        total_seconds = int(remaining.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    @property
    def duration_used_display(self):
        if self.ended_at:
            delta = self.ended_at - self.started_at
        else:
            delta = timezone.now() - self.started_at
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes}m"

    @property
    def data_used_display(self):
        if self.data_used_mb >= 1024:
            return f"{self.data_used_mb / 1024:.2f} GB"
        return f"{self.data_used_mb:.1f} MB"

    def terminate(self, reason='manual'):
        self.status = 'terminated'
        self.ended_at = timezone.now()
        self.terminated_by = reason
        self.save()
        # Update client status
        self.client.status = 'inactive'
        self.client.save()