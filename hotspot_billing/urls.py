from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ── CAPTIVE PORTAL (default for WiFi clients) ────
    path('', include('clients.portal_urls')),  # This is what users see first
    
    # ── ADMIN/STAFF URLS ─────────────────────────────
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('clients/', include('clients.urls')),
    path('packages/', include('packages.urls')),
    path('payments/', include('payments.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)