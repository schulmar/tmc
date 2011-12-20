import json 
import urllib2, urllib

"""
\file ManiaConnect.py
\brief Holds all classes needed, to manage ManiaConnect Sessions
"""

class HTTPClient(object):
    """
    \brief The client will connect to the system and authenticate itself
    """
    __VERSION = '1.1' #The client version 
    __USER_AGENT = 'maniaplanet-ws-sdk/' #The useragent of this client
    code = None #The code that was passed by the request
    
    def __init__(self, userName = None, password = None):
        """
        \brief Create a new client
        \param userName The name of the user to authenticate
        \param password His password
        """
        self._apiUrl = 'https://ws.maniaplanet.com' #The API URL of the MP-Webservices
        self._userName = userName #The name of the user to connect with
        self._password = password #The password of this user
        self._enableAuth = True #Should basic HTTP autentification be used
        self._headers = {} #Additional headers for the request
        self._accept = 'application/json' #The type of data accepted from request
        self._contentType = 'application/json' #The type of data sent to the request
        self._serializeCallback = json.dumps #The callback for serialization
        self._unserializeCallback = json.loads #The callback for unserialization
        
    def execute(self, method, ressource, data = None):
        """
        \brief Execute an HTML request
        \param method The method to use (POST, GET, ...)
        \param ressource The path to the ressource to call
        \param data The data to post
        """
        url = self._apiUrl + ressource
        if method == 'POST':
            if data != None:
                if self._serializeCallback != None:
                    data = self._serializeCallback(data)
        elif method == 'GET':
            data = None
        else:
            raise ('Unknown method ' + method)
            return None
        
        director = urllib2.OpenerDirector()
        
        if self._enableAuth:
            manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            manager.add_password(None, url, self._userName, self._password)
            handler = urllib2.HTTPBasicAuthHandler(manager)
            director.add_handler(handler)
        
        headers = dict({
                  'Accept' : self._accept,
                  'Content-type' : self._contentType,
                  'User-Agent' : self.__USER_AGENT + self.__VERSION
                  }.items() + self._headers.items())
                  
        request = urllib2.Request(url, data, headers)
        
        result = director.open(request)
        
        if result.info()['http_code'] == 200:
            return self._unserializeCallback(result.info().read())
        
        raise 'Invalid response code ' + str(result.info()['http_code'])
    
class Client(HTTPClient):
    """
    \brief The client class that handles the connection to the MP Webservices
    """
    #The url where to authorize
    _authorizationURL = 'https://ws.maniaplanet.com/oauth2/authorize/'
    #The logout url
    _logoutURL = 'https://ws.maniaplanet.com/oauth2/authorize/logout/'
    #The path to the oauth2 token
    _tokenPath = '/oauth2/token/'
    #The persistance object
    _persistance = None
    
    @staticmethod
    def setPersistance(self, newPersistance):
        """
        \brief Set the static persistance object
        \param newPersistance The new persistance object
        """
        Client._persistance = newPersistance
        
    def __init__(self, userName = None, password = None):
        """
        \brief Construct a new client instance
        \param userName The username to login
        \param password The password to login
        """
        super(Client, self).__init(userName, password)
        Client._persistance.init()
        
    def getLoginUrl(self, redirectURI, scope = None):
        """
        \brief When a user is not authentified, you need to create a link to 
                the URL returned by this method.
        \param redirectUri  Where to redirect the user after auth.
        \param scope Space-separated list of scopes. Leave empty if you just need the basic one
        """
        self._persistance.setVariable('redirect_uri', redirectURI)
        if scope != None:
            return self.getAuthorizationURL(redirectURI, scope)
        else:
            return self.getAuthorizationURL(redirectURI)
    
    def getLogoutUrl(self, redirectURI):
        """
        \brief If you want to place a "logout" button, you can use this link to log the 
                 user out of the player page too. Don't forget to empty your sessions.
        \param redirectURI Where to redirect the user after he logged out
        """
        return self._logoutURL + '?' + urllib.urlencode({'redirect_uri':redirectURI})
    
    def logout(self):
        """
        \brief Destroys the persistance
        """
        self._persistance.destroy()
        
    def getAuthorizationURL(self, redirectURI, scope = 'basic'):
        """
        \brief  Get the url for authorization
        \param redirectURI Where to redirect after authorization
        \param scope The scopes to authorize
        """
        return self._authorizationURL + '?' + urllib.urlencode(
                        {
                         'client_id'    : self._userName,
                         'redirect_uri' : redirectURI,
                         'scope'        : scope,
                         'response_type': 'code' 
                         })
        
    def getAccessToken(self):
        """
        \brief Tries to get an access token.
            
         If one is found in the session, it returns it.
         If a code is found in the request, it tries to exchange it for an access
         token on the OAuth2 Token Endpoint
         Else it returns false
        """
        token = self._persistance.getVariable('access_token')
        if token != None:
            return token
        else:
            redirectUri = self._persistance.getVariable('redirect_uri')
            accessToken = self.getAccessTokenFromCode(self.code, redirectUri)
            self._persistance.setVariable('access_token', accessToken)
            return accessToken
        
    def getAccessTokenFromCode(self, authorizationCode, redirectURI):
        """
        \brief Get the access token from an authorizationCode
        \param authorizationCode ...
        \param redirectURI As usual
        """
        contentType = self._contentType
        self._contentType = 'application/x-www-form-urlencoded'
        serializeCallback = self._serializeCallback
        self._serializeCallback = None
        
        params = urllib.urlencode({
                   'client_id'      : self._userName,
                   'client_secret'  : self._password,
                   'redirect_uri'   : redirectURI,
                   'grant_type'     : 'authorization_code',
                   'code'           : authorizationCode
                                   })
        try:
            response = self.execute('POST', self._tokenPath, params)
        except Exception as e:
            print(str(e))
        
        self._serializeCallback = serializeCallback  
        self._contentType = contentType
        
        self._persistance.deleteVariable('redirect_uri')
        self._persistance.deleteVariable('code')
        #TODO: is this correct or should this be a dictionary access?
        return response.access_token
    
    def executeOAuth2(self, method, ressource, params = None):
        """
        \brief USing OAuth2 for authentication,
        """
        self._headers = {'Authorization' : 
                         'Bearer {0}'.format(self._persistance.getVariable('access_token'))}
        self._enableAuth = False
        try:
            result = self.execute(method, ressource, params)
            self._enableAuth = True
            return result
        except:
            self._enableAuth = True
            raise
        
class Player(Client):
    """
    \brief The base class for using OAuth2
    """
    def getPlayer(self):
        """
         This is the first method to call when you have an authorization code. 
         It will retrieve an access token if possible and then call the service to
         retrieve a basic object about the authentified player. 
         
         You do not need any special scope to call this service, as long as you 
         have an access token.
         
         If an access token is not found, it will return false
         
         \return A player object or false if no access token is found
        """
        player = self._persistance.getVariable('player')
        if player == None:
            if self.getAccessToken() != None:
                player = self.executeOAuth2('GET', '/player/')
                self._persistance.setVariable('player', player)
        return player        
    
    def getOnlineStatus(self):
        """
        \brief Returns an object containing the online status and the dedicated server 
                 info on which the player is playing, if applicable.
         
        Scope needed: online_status
        """
        return self.executeOAuth2('GET', '/player/status/')
    
    def getEmail(self):
        """
        \brief Returns the email associated with the player's account.
        \return string with the email
        Scope needed: email
        """
        return self.executeOAuth2('GET', '/player/email/')
    
    def getBuddies(self):
        """
        \brief Returns the buddies of the player as a list of player objects
     
        Scope needed: buddies
        """
        return self.executeOAuth2('GET', '/player/buddies/')
    
    def getDedicated(self):
        """
        \brief Gets the list of the player's registered dedicated servers and their 
                 online statuses.
        Scope needed: dedicated
        """
        return self.executeOAuth2('GET', '/player/dedicated/')
    
    def getManialinks(self):
        """
        \brief Gets the list of the player's registered Manialinks.
        
        Scope needed: manialinks
        """
        return self.executeOAuth2('GET', '/player/manialinks/')
    
class Persistance(object):
    """
    \brief A basic interface of persistance obects
    """
    def __init__(self):
        super(Persistance, self).__init__()
    def init(self):
        pass
    def destroy(self):
        pass
    def getVariable(self, name, default = None):
        pass
    def setVariable(self, name, value):
        pass
    def deleteVariable(self, name):
        pass
    
class PersistanceDict(Persistance):
    def __init__(self):
        super(PersistanceDict, self).__init__()
        
    def init(self):
        self.__dict = {}
        
    def destroy(self):
        del self.__dict
        
    def getVariable(self, name, default = None):
        try:
            return self.__dict[name]
        except KeyError:
            return default
        
    def setVariable(self, name, value):
        self.__dict[name] = value
        
    def deleteVariable(self, name):
        try:
            del self.__dict[name]
        except KeyError:
            pass