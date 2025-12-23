import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alvarez_bakery.settings')

# Import Django and setup
import django
django.setup()

# Import the WSGI application
application = get_wsgi_application()

# Vercel expects a class-based handler
class handler:
    def __init__(self):
        self.application = application
    
    def __call__(self, environ, start_response):
        return self.application(environ, start_response)
