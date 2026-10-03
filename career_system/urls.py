"""
career_system/urls.py
Master URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    # Django admin panel
    path('admin/', admin.site.urls),

    # Landing page
    path('', core_views.landing_page, name='landing'),

    # Authentication (register, login, logout, profile)
    path('accounts/', include('accounts.urls')),

    # Core system (dashboard, grades, quiz, results, report)
    path('', include('core.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
