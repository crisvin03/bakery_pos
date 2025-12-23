import os
import sys
from http.server import BaseHTTPRequestHandler
from io import BytesIO

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alvarez_bakery.settings')

# Import Django and setup
import django
django.setup()

# Import the WSGI application
from django.core.wsgi import get_wsgi_application
_application = get_wsgi_application()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        return self._handle_request()
    
    def do_POST(self):
        return self._handle_request()
    
    def do_PUT(self):
        return self._handle_request()
    
    def do_DELETE(self):
        return self._handle_request()
    
    def do_PATCH(self):
        return self._handle_request()
    
    def _handle_request(self):
        # Build WSGI environ from HTTP request
        environ = {
            'REQUEST_METHOD': self.command,
            'SCRIPT_NAME': '',
            'PATH_INFO': self.path.split('?')[0],
            'QUERY_STRING': self.path.split('?')[1] if '?' in self.path else '',
            'CONTENT_TYPE': self.headers.get('Content-Type', ''),
            'CONTENT_LENGTH': self.headers.get('Content-Length', '0'),
            'SERVER_NAME': self.headers.get('Host', 'localhost').split(':')[0],
            'SERVER_PORT': '443',
            'SERVER_PROTOCOL': self.request_version,
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https',
            'wsgi.input': BytesIO(self.rfile.read(int(self.headers.get('Content-Length', 0)))),
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }
        
        # Add HTTP headers to environ
        for key, value in self.headers.items():
            key = key.replace('-', '_').upper()
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                environ[f'HTTP_{key}'] = value
        
        # Response data
        response_status = None
        response_headers = []
        
        def start_response(status, headers):
            nonlocal response_status, response_headers
            response_status = status
            response_headers = headers
        
        # Call Django WSGI application
        response_body = b''.join(_application(environ, start_response))
        
        # Send response
        status_code = int(response_status.split()[0])
        self.send_response(status_code)
        
        for header_name, header_value in response_headers:
            self.send_header(header_name, header_value)
        self.end_headers()
        
        self.wfile.write(response_body)
