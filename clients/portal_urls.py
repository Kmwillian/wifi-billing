from django.urls import path
from . import portal_views

urlpatterns = [
    path('', portal_views.CaptivePortalView.as_view(), name='portal_home'),
    path('connect/', portal_views.InitiatePaymentView.as_view(), name='portal_connect'),
    path('status/', portal_views.ConnectionStatusView.as_view(), name='portal_status'),
    path('success/', portal_views.PaymentSuccessView.as_view(), name='portal_success'),
]