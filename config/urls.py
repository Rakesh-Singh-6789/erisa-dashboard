"""
URL configuration for ERISA Assessment project.
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static


def logout_view(request):
    """Custom logout view that accepts both GET and POST requests"""
    logout(request)
    return redirect('/login/')


# Core URL patterns
urlpatterns = [
    # Admin URLs (configurable in production)
    path(getattr(settings, 'ADMIN_URL', 'admin/'), admin.site.urls),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),
    path('logout/', logout_view, name='logout'),
    
    # App URLs
    path('', include('apps.claims.urls')),
]

# Development-only URLs
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, 
        document_root=settings.MEDIA_ROOT
    )
    
    # Add debug toolbar URLs if available
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Custom error handlers
handler400 = 'apps.core.views.error_400'
handler403 = 'apps.core.views.error_403'
handler404 = 'apps.core.views.error_404'
handler500 = 'apps.core.views.error_500'