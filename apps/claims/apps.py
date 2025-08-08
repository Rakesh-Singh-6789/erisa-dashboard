"""
Claims app configuration.
"""
from django.apps import AppConfig


class ClaimsConfig(AppConfig):
    """Configuration for the claims app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.claims'
    verbose_name = 'Claims Management'
    
    def ready(self):
        """Import signal handlers when the app is ready."""
        # Import signals here to avoid circular imports
        try:
            from . import signals
        except ImportError:
            pass