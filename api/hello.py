from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        message = '{"message": "Hello from Podunk Pantry!"}'
        self.wfile.write(message.encode('utf-8'))
        return
