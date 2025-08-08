"""
Core views for error handling and common functionality.
"""
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.views.generic import TemplateView
import logging

logger = logging.getLogger(__name__)


class BaseView(TemplateView):
    """Base view class with common functionality."""
    
    def get_context_data(self, **kwargs):
        """Add common context data to all views."""
        context = super().get_context_data(**kwargs)
        context.update({
            'app_name': 'ERISA Assessment',
            'app_version': '1.0.0',
        })
        return context


def error_400(request: HttpRequest, exception=None) -> HttpResponse:
    """Handle 400 Bad Request errors."""
    logger.warning(f"400 error for {request.path}")
    return render(
        request, 
        'errors/400.html', 
        {'request_path': request.path},
        status=400
    )


def error_403(request: HttpRequest, exception=None) -> HttpResponse:
    """Handle 403 Forbidden errors."""
    logger.warning(f"403 error for {request.path}")
    return render(
        request, 
        'errors/403.html', 
        {'request_path': request.path},
        status=403
    )


def error_404(request: HttpRequest, exception=None) -> HttpResponse:
    """Handle 404 Not Found errors."""
    logger.info(f"404 error for {request.path}")
    return render(
        request, 
        'errors/404.html', 
        {'request_path': request.path},
        status=404
    )


def error_500(request: HttpRequest) -> HttpResponse:
    """Handle 500 Internal Server errors."""
    logger.error(f"500 error for {request.path}")
    return render(
        request, 
        'errors/500.html', 
        {'request_path': request.path},
        status=500
    )