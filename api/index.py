import os
import sys
import traceback

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alvarez_bakery.settings')

try:
    # Import Django after setting up the environment
    import django
    django.setup()
    
    # Import the WSGI application
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    
    print("Django application initialized successfully")
    
except Exception as e:
    print(f"Error initializing Django: {str(e)}")
    print(f"Traceback: {traceback.format_exc()}")
    raise

# Vercel serverless handler
def handler(environ, start_response):
    try:
        return application(environ, start_response)
    except Exception as e:
        print(f"Handler error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return [f'Internal Server Error: {str(e)}'.encode()]
