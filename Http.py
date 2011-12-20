import BaseHTTPServer
import urlparse
from PluginInterface import *
from Manialink import *
import random
import string
import time
import urllib2
import math
import ManiaConnect
import Cookie

"""
\file http.py
\brief Contains the http plugin for uploads via http
"""

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_POST(self):
		self.send_response(200)
		self.send_header('Content-Type', 'text/xml')
		self.end_headers()
		entries = urlparse.parse_qs(self.path.split('?')[-1])
		for k in entries:
			if len(entries[k]) == 1:
				entries[k] = entries[k][0]
		token = entries['token']
		data = self.rfile.read(int(self.headers.getheader('content-length')))
		manialink = self.server.plugin.dataRecieved(token, entries, data)
		self.wfile.write(manialink)
		
	def do_GET(self):
		content, session = self.server.plugin.handleGet(self.path)
		self.send_response(200)
		self.send_header('Content-Type', 'text/xml')
		if session != None:
			self.send_header('Set-Cookie', 'session=' + str(session))
		self.end_headers()  
		self.wfile.write(content)

class Http(PluginInterface):
	"""
	\brief A class for uploads using the http protocol
	"""
	
	def __init__(self, pipes, args):
		"""
		\brief Construct the Plugin
		\param pipes The pipes to the PluginManager process
		\arrs Additional plugin start arguments
		"""
		super(Http, self).__init__(pipes)
		self.__httpd = None#the server instance
		self.__address = None#the server address
		self.__thread = None#the thread in which the http server will run
		self.__usedTokens = {}#a dict that maps tokens to their callback
		self.__expiration_time = 100#the time a token stays valid in seconds
		self.__registeredPaths = {} #Paths that were registered to callbacks
		self.__sessions = {} #The sessions per user
		
	def initialize(self, args):
		"""
		\brief Start up the http server
		\args Contains the connection data in a dictionary
		
		The server needs: address : ip or domain name (leave empty for autodetection)
						 port : the port (necessary)
		"""
		self.__ManiaConnect = {'username' : args['user'],
								'password' : args['password']}
		self.registerPath('/login/test/', ('Http', 'loginTest'))
		try:
			#read the address if given
			self.__address = args['address']
		except KeyError:
			self.log("Determining the public ip, as none was given by the user")
			#try to get the ip from the internet if the address was not given
			try:
				self.__address = urllib2.urlopen("http://whatismyip.org/").read()
				self.log("Public ip is " + str(self.__address))
			except:
				self.__address = '127.0.0.1'
				self.log("Error: Could not determine public ip")
				print("Error: Could not determine public ip")
			
		self.__address = (self.__address, args['port'])
		self.__httpd = BaseHTTPServer.HTTPServer(('', args['port']), Handler)
		self.__httpd.plugin = self
		self.__thread = threading.Thread(target = self.__httpd.serve_forever)
		self.__thread.daemon = True
		self.__thread.start()
		
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
		i = int(5 + math.log(1 + len(self.__usedTokens)))
		token = getToken(i)
		while token in self.__usedTokens:
			i += 1
			token = getToken(i)
		#safe the callback for the token and its age
		self.__usedTokens[token] = (callback, args, time.time() + self.__expiration_time)
		#return the token to the caller
		return (token, self.__address)
	
	@staticmethod
	def dataRecievedCallbackSignature(entries, data, *userSpecifiedArguments):
		"""
		\brief The POST upload callback signature
		\param entries The values of the form entries
		\param data The data that were posted
		\param userSpecifiedArguments Additional arguments that were defined
			by the caller of getUploadToken
		"""
	
	def dataRecieved(self, token, entries, data):
		"""
		\brief Calling the callback when data for the token were recieved
		\param token The token that was used
		\param entries All GET parameters
		\param data The raw POST data 
		"""
		if token in self.__usedTokens and self.__usedTokens[token][2] >= time.time():
			tokenDictEntry = self.__usedTokens[token] 
			xml = self.callFunction(tokenDictEntry[0], entries, data, *tokenDictEntry[1])
			#remove token from dict as it was used
			del self.__usedTokens[token]
			return xml
		else:
			if token in self.__usedTokens:
				del self.__usedTokens[token]
				return '''<?xml version="1.0" encoding="utf-8" ?>
				<manialink>
					<label text="$f12$oError$o$fff: The token you used has expired" />
				</manialink>'''
			else:
				return '''<?xml version="1.0" encoding="utf-8" ?>
				<manialink>
					<label text="$f12$oError$o$fff: The token you used is not valid" />
				</manialink>'''

	def registerPath(self, path, callback, *args):
		"""
		\brief Register a path to handle
		\param path The path to register for
		\param callback The callback that should return the data
		"""
		if path in self.__registeredPaths:
			self.log('Warning: Path ' + path + ' is already registered to ' + str(self.__registeredPaths[path][0]))
			
		self.__registeredPaths[path] = (callback, args)
		
	@staticmethod
	def getCallbackSignature(entries, login, *additionalParams):
		"""
		\brief The signature for get Callbacks
		\param entries The dictionary for the url query
		\param login The login of the calling player
		\param additionalParams Predefined params to send
		"""
		
	def handleGet(self, path, sessionId):
		"""
		\brief Handle a get request
		\param path The full URL
		\param session The session that was used (or None)
		"""
		parsed = urlparse.urlparse(path)
		query = urlparse.parse_qs(parsed.query)
		if 'code' in query:
			sessionId = query['code']
			expires, session = (time.time() + self.__expiration_time,
							ManiaConnect.Player(self.__ManiaConnect['username'],
												self.__ManiaConnect['password']))
			session.code = sessionId
			self.__sessions[sessionId] = (expires, session) 
			
		try:
			callback = self.__registeredPaths[parsed.path]
		except KeyError:
			return ('''
			<?xml version="1.0" encoding="utf-8" ?>
			<manialink>
				<label text="$f12$oError$o$fff: The ressource you requested is not valid!" />
			</manialink>
			''', None)
		try:
			expires, session = self._sessions[sessionId]
		except KeyError:
			Player = ManiaConnect.Player(self.__ManiaConnect['username'],
										self.__ManiaConnect['password'])
			xml = '''
				<?xml version="1.0" encoding="utf-8" ?>
				<manialink>
					<label text="$f12$oError$o$fff: Could not find your session, please authenticate again!" />
					<label posn="0 -3" text ="Authenticate" manialink="{0}" />
				</manialink>
			'''.format(Player.getLoginUrl(path))
			return (xml, None)
			
		if expires < time.time():
			del self.__sessions[sessionId]
			Player = ManiaConnect.Player(self.__ManiaConnect['username'],
										self.__ManiaConnect['password'])
			xml = '''
				<?xml version="1.0" encoding="utf-8" ?>
				<manialink>
					<label text="$f12$oError$o$fff: Your session has expired, please authenticate again!" />
					<label posn="0 -3" text ="Authenticate" manialink="{0}" />
				</manialink>
			'''.format(Player.getLoginURL(path))
			return (xml, None)
		else:	
			#Refresh the session
			self.__sessions[sessionId] = (time.time() + self.__expiration_time,
										session)
			return (self.callFunction(callback[0], session.getPlayer()['login'], 
									urlparse.parse_qs(parsed.query), *callback[1])
					, sessionId)
		
	def loginTest(self, entries, login):
		"""
		\brief A login test for the ManiaConnect API
		\param entries The query dict
		\login The login of the calling player
		"""
		return '''
			<?xml version="1.0" encoding="utf-8" ?>
			<manialink>
				<label text="{0}" />
				<label posn="0 -3" text ="Login: {1}" />
			</manialink>
		'''.format(str(entries), login)