from django.urls import path
from . import views

app_name = 'packages'

urlpatterns = [
    path('', views.PackageListView.as_view(), name='list'),
    path('add/', views.PackageCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.PackageUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.package_delete_view, name='delete'),
    path('<int:pk>/toggle/', views.package_toggle_status, name='toggle_status'),
    path('<int:pk>/api/', views.package_detail_api, name='detail_api'),
]