from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.PaymentListView.as_view(), name='list'),
    path('<int:pk>/', views.payment_detail_view, name='detail'),
    path('manual/', views.ManualActivationView.as_view(), name='manual_activation'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('check/<int:payment_id>/', views.check_payment_status, name='check_status'),
    path('api/revenue-chart/', views.revenue_chart_api, name='revenue_chart'),
]