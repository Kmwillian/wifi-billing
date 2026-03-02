from django.db import models
from django.utils import timezone
from clients.models import Client, Session
from packages.models import Package


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('cash', 'Cash'),
        ('manual', 'Manual Activation'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments'
    )
    package = models.ForeignKey(
        Package,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments'
    )
    session = models.OneToOneField(
        Session,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment'
    )

    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone = models.CharField(max_length=15)
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        default='mpesa'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    # M-Pesa specific fields
    checkout_request_id = models.CharField(max_length=100, blank=True, db_index=True)
    merchant_request_id = models.CharField(max_length=100, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True, unique=True, null=True)
    mpesa_transaction_date = models.CharField(max_length=20, blank=True)

    # Timestamps
    initiated_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Raw callback data for debugging
    raw_callback = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"{self.client} — KES {self.amount} [{self.status}]"

    @property
    def is_completed(self):
        return self.status == 'completed'

    @property
    def is_pending(self):
        return self.status == 'pending'


class ManualActivation(models.Model):
    """
    Track manual session activations done by staff
    e.g. when a client pays cash
    """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='manual_activations')
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True)
    activated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='activations'
    )
    payment = models.OneToOneField(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)
    activated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-activated_at']
        verbose_name = 'Manual Activation'
        verbose_name_plural = 'Manual Activations'

    def __str__(self):
        return f"{self.client} — {self.package} by {self.activated_by}"