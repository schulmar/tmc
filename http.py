import BaseHTTPServer
import urlparse
from PluginInterface import *
import random
import string
import time

"""
\file http.py
\brief Contains the http plugin for uploads via http
"""

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_POST(self):
		print(urlparse.parse_qs(self.path.split('?')[-1]))
		self.send_response(200)
		self.send_header('Content-Type', 'text/xml')
		self.end_headers()
		self.wfile.write('<?xml version="1.0" encoding="utf-8" ?><manialink><label text="Thank you"/></manialink>')

class HttpUploads(PluginInterface):
	"""
	\brief A class for uploads using the http protocol
	"""
	__httpd = None#the server instance
	__usedTokens = {}#a dict that maps tokens to their callback
	__expiration_time = 100#the time a token stays valid in seconds
	
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
		
	def getUploadToken(self, callback, *args):
		"""
		\brief Generates a valid token for 
		"""
		def getToken(N):
			return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(N))
		#search a free token
		i = 5
		token = getToken(i)
		while token in self.__usedTokens:
			i += 1
			token = getToken(i)
		#safe the callback for the token and its age
		self.__usedTokens[token] = (callback, args, time.time() + self.__expiration_time)
		#return the token to the caller
		return token
	
	def dataRecieved(self, token, entries, data):
		"""
		\brief Calling the callback when data for the token were recieved
		\param token The token that was used
		\param entries All GET parameters
		\param data The raw POST data 
		"""
		if token in self.__usedTokens and self.__usedTokens[token][2] >= time.time():
			pass
