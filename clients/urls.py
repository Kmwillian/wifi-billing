from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.ClientListView.as_view(), name='list'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='detail'),
    path('add/', views.ClientCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.ClientUpdateView.as_view(), name='update'),
    path('<int:pk>/block/', views.client_block_view, name='block'),
    path('sessions/', views.active_sessions_view, name='active_sessions'),
    path('sessions/<int:session_id>/terminate/', views.terminate_session_view, name='terminate_session'),
    path('api/session-stats/', views.session_stats_api, name='session_stats_api'),
]  