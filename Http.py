import BaseHTTPServer
import urlparse
from PluginInterface import *
import random
import string
import time
import urllib

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
		entries = urlparse.parse_qs(self.path.split('?')[-1])
		token = entries['token']
		data = self.rfile.Read()
		manialink = self.server.__plugin.dataRecieved(token, entries, data)
		self.wfile.write(manialink)

class Http(PluginInterface):
	"""
	\brief A class for uploads using the http protocol
	"""
	__httpd = None#the server instance
	__address = None#the server address
	__usedTokens = {}#a dict that maps tokens to their callback
	__expiration_time = 100#the time a token stays valid in seconds
	
	def __init__(self, pipes, args):
		"""
		\brief Construct the Plugin
		\param pipes The pipes to the PluginManager process
		\arrs Additional plugin start arguments
		"""
		super(Http, self).__init__(pipes)
		
	def initialize(self, args):
		"""
		\brief Start up the http server
		\args Contains the connection data in a dictionary
		
		The server needs: address : ip or domain name (leave empty for autodetection)
						 port : the port (necessary)
		"""
		try:
			#read the address if given
			self.__address = args['address']
		except KeyError:
			#try to get the ip from the internet if the address was not given
			self.__address = urllib.urlopen("http://whatismyip.org/").read()
			
		self.__address = (self.__address, args['port'])
		self.__httpd = BaseHTTPServer.HTTPServer(self.__address, Handler)
		self.__httpd.__plugin = self
		self.__thread = threading.Thread(target = self.__httpd.serve_forever())
		self.__thread.run()
		
	def getUploadToken(self, callback, *args):
		"""
		\brief Generates a valid token for direct http uploads
		\param callback the function to call when the token is used
		\param args Additional parameters to pass to the function
		\return (the token, the (address, ip)-tuple of the upload server)
		
		The callback has following signature:
		(entries, data, *args)
		Where args are the userdefined args passed to this function
		To get this working the calling form must use the GET variable "token"
		with the passed value
		"""
		getToken = lambda N: ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(N))
		#search a free token
		i = 5
		token = getToken(i)
		while token in self.__usedTokens:
			i += 1
			token = getToken(i)
		#safe the callback for the token and its age
		self.__usedTokens[token] = (callback, args, time.time() + self.__expiration_time)
		#return the token to the caller
		return (token, self.__address)
	
	def dataRecieved(self, token, entries, data):
		"""
		\brief Calling the callback when data for the token were recieved
		\param token The token that was used
		\param entries All GET parameters
		\param data The raw POST data 
		"""
		if token in self.__usedTokens and self.__usedTokens[token][2] >= time.time():
			tokenDictEntry = self.__usedTokens[token] 
			return self.callFunction(tokenDictEntry[0], entries, data, *tokenDictEntry[1])
		else:
			return '''<?xml version="1.0" encoding="utf-8" ?>
			<manialink>
				<label text="$f12$bError$b$000: The token you used is not valid" />
			</manialink>'''
