from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('staff/', views.StaffListView.as_view(), name='staff_list'),
    path('staff/add/', views.StaffCreateView.as_view(), name='staff_create'),
    path('staff/<int:pk>/edit/', views.StaffUpdateView.as_view(), name='staff_update'),
    path('staff/<int:pk>/delete/', views.staff_delete_view, name='staff_delete'),
    path('profile/', views.profile_view, name='profile'),
    path('audit-log/', views.audit_log_view, name='audit_log'),
]