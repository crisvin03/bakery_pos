from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alvarez_bakery.settings')

# Import Django and setup
import django
django.setup()

# Import the WSGI application
from django.core.wsgi import get_wsgi_application
from io import BytesIO

_application = get_wsgi_application()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request()
    
    def do_POST(self):
        self.handle_request()
    
    def do_PUT(self):
        self.handle_request()
    
    def do_DELETE(self):
        self.handle_request()
    
    def do_PATCH(self):
        self.handle_request()
    
    def handle_request(self):
        try:
            # Parse the URL
            parsed_path = urlparse(self.path)
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b''
            
            # Build WSGI environ
            environ = {
                'REQUEST_METHOD': self.command,
                'SCRIPT_NAME': '',
                'PATH_INFO': parsed_path.path,
                'QUERY_STRING': parsed_path.query,
                'CONTENT_TYPE': self.headers.get('Content-Type', ''),
                'CONTENT_LENGTH': str(content_length),
                'SERVER_NAME': self.headers.get('Host', 'localhost').split(':')[0],
                'SERVER_PORT': '443',
                'SERVER_PROTOCOL': self.request_version,
                'wsgi.version': (1, 0),
                'wsgi.url_scheme': 'https',
                'wsgi.input': BytesIO(body),
                'wsgi.errors': sys.stderr,
                'wsgi.multithread': False,
                'wsgi.multiprocess': False,
                'wsgi.run_once': False,
            }
            
            # Add HTTP headers
            for key, value in self.headers.items():
                key = key.replace('-', '_').upper()
                if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                    environ[f'HTTP_{key}'] = value
            
            # Response storage
            self.response_status = None
            self.response_headers = []
            
            def start_response(status, headers, exc_info=None):
                self.response_status = status
                self.response_headers = headers
                return lambda s: None
            
            # Call Django WSGI app
            response_data = _application(environ, start_response)
            response_body = b''.join(response_data)
            
            # Send response
            status_code = int(self.response_status.split()[0])
            self.send_response(status_code)
            
            for header_name, header_value in self.response_headers:
                self.send_header(header_name, header_value)
            self.end_headers()
            
            self.wfile.write(response_body)
            
        except Exception as e:
            # Send error response
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            error_msg = f'Internal Server Error: {str(e)}'
            self.wfile.write(error_msg.encode())
