# healthcheck.py
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
import sys

class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            # Try to connect to the database
            db_conn = connections['default']
            db_conn.cursor()
            
            # Exit with 0 if healthy
            sys.exit(0)
        except OperationalError:
            # Exit with 1 if unhealthy
            sys.exit(1)