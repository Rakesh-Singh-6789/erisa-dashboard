"""
Core app configuration.
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the core app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core'
    
    def ready(self):
        """Import signal handlers when the app is ready."""
        # Import signals here to avoid circular imports
        pass