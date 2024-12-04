# apps.py

from django.apps import AppConfig

class HotelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hotel'

    def ready(self):
        """Initialize services when Django starts"""
        import os
        if os.environ.get('RUN_EVENT_STREAM') == 'true':
            from hotel.event_handler import start_event_stream
            start_event_stream()