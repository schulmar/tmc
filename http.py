import BaseHTTPServer
import urlparse
from PluginInterface import *
import md5

"""
\file http.py
\brief Contains the http plugin for uploads via http
"""

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

class HttpUploads(PluginInterface):
	"""
	\brief A class for uploads using the http protocol
	"""
	__httpd = None#the server instance
	
	def __init__(self, pipes, args):
		"""
		\brief Construct the Plugin
		\param pipes The pipes to the PluginManager process
		\arrs Additional plugin start arguments
		"""
		super(HttpUploads, self).__init__(pipes)
		
	def initialize(self, args):
		"""
		\brief Start up the http server
		\args Contains the connection data in a dictionary
		
		The server needs: address : (ip, port)
		"""
		self.__httpd = BaseHTTPServer.HTTPServer(args['address'], Handler)
		self.__httpd.__plugin = self
		self.__httpd.serve_forever()
		
	def getUploadToken(self, callback):
		token = md5.new
