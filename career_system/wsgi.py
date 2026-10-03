"""career_system/wsgi.py"""
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'career_system.settings')
application = get_wsgi_application()
