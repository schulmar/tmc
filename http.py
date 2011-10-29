import BaseHTTPServer
import urlparse

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_POST(self):
		print(self)
		print(self.headers)
		print(urlparse.parse_qs(self.path.split('?')[-1]))
		print(self.command)
		print(self.client_address)
		self.send_response(200)
		self.send_header('Content-Type', 'text/xml')
		self.end_headers()
		self.wfile.write('<?xml version="1.0" encoding="utf-8" ?><manialink><label text="Thank you"/></manialink>')

address = ('', 8888)
httpd = BaseHTTPServer.HTTPServer(address, Handler)
httpd.serve_forever()
