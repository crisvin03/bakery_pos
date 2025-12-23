import os
import sys
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alvarez_bakery.settings')

logger.info("Starting Django application initialization...")

try:
    # Import Django after setting up the environment
    import django
    logger.info("Django imported successfully")
    
    django.setup()
    logger.info("Django setup completed successfully")
    
    # Import the WSGI application
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    
    logger.info("Django WSGI application initialized successfully")
    
except Exception as e:
    logger.error(f"Error initializing Django: {str(e)}")
    logger.error(f"Full traceback: {traceback.format_exc()}")
    raise

# Vercel serverless handler
def handler(environ, start_response):
    logger.info(f"Handler called with path: {environ.get('PATH_INFO', '/')}")
    
    try:
        logger.info("Calling Django application...")
        response = application(environ, start_response)
        logger.info("Django application returned response")
        return response
        
    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Return a proper HTTP error response
        error_body = f"Internal Server Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        start_response('500 Internal Server Error', [
            ('Content-Type', 'text/plain'),
            ('Content-Length', str(len(error_body.encode())))
        ])
        return [error_body.encode()]
