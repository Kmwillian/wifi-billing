from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardHomeView.as_view(), name='home'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('api/live-stats/', views.live_stats_api, name='live_stats'),
]
