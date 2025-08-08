"""
Core app configuration.
"""
from django.apps import AppConfig
from django.db.backends.signals import connection_created


class CoreConfig(AppConfig):
    """Configuration for the core app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core'
    
    def ready(self):
        """Import signal handlers when the app is ready."""
        # Configure SQLite for better concurrency: WAL + NORMAL sync
        def set_sqlite_pragmas(sender, connection, **kwargs):
            if connection.vendor == 'sqlite':
                with connection.cursor() as cursor:
                    cursor.execute('PRAGMA journal_mode=WAL;')
                    cursor.execute('PRAGMA synchronous=NORMAL;')

        connection_created.connect(set_sqlite_pragmas)