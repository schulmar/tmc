from PluginInterface import *
import MySQLdb
import os
import urllib
import json
from Manialink import *
import base64
from WindowElements import *

"""
\file Maps.py
\brief Contains the Maps plugin

This plugin should manage the maps on the server
"""

class Maps(PluginInterface):
	"""
	\brief The Maps plugin class derived from PluginInterface
	"""	
	__MapObjectType = 'Maps.map' #the objectTypeName of maps for the karma system
	__writeCommentWindowName = 'Maps.writeComment' #The name of the comment window
	__displayCommentsWindowName = 'Maps.displayComment' #The name of the comments window
	__addCommentRight = 'Maps.addComment' #The name of the right to add comments to maps
	__editOwnCommentsRight = 'Maps.editOwnComments' #The name of the right to edit ones own comments
	__editOthersCommentsRight = 'Maps.editOthersComments' #The name of the right to edit others comments
	
	def __init__(self, pipes, args):
		"""
		\brief Construct the class
		\param pipes The pipes to the PluginManager process
		\param args Additional userdefined args 
		"""
		self.__currentMaps = []#List of the maps that currently run on the server
		self.__currentMap = None#The current map
		self.__nextMap = None #The next map
		self.__mxPath = 'mania-exchange/'#The name of the folder into which mania-exchange maps will be downloaded
		self.__connection = None#The database connection
		self.__matchSettingsFileName = 'tracklist.txt' #The name of the matchsettings file
		self.__jukebox = [] #List of tracks that are currently in the jukebox (track, loginOfJuker)
		self.__playerDict = {} #a dictionary that contains the index mapping of the tracks per user
		super(Maps, self).__init__(pipes)

	def initialize(self, args):
		"""
		\brief Initialize the plugin on startup
		\params args The user parameters for the plugin
		
		Setup the database connection create tables if necessary...
		""" 
		self.__args = args #save the database login
		self.__connection = MySQLdb.connect(user = args['user'], passwd = args['password'], db = args['db'])
		cursor = self.__connection.cursor()
		cursor.execute("SHOW TABLES")
		tables = [i[0] for i in cursor.fetchall()]
		if not 'maps' in tables:
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS `maps` (
				`Id` mediumint(9) NOT NULL auto_increment, 
				`Uid` varchar(27) NOT NULL default '', 
				`Name` varchar(100) NOT NULL default '',
				`Author` varchar(30) NOT NULL default '',
				`Environment` varchar(10) NOT NULL default '',
				PRIMARY KEY (`Id`),
				UNIQUE KEY `Uid` (`Uid`)
				);
			""");
		cursor.close()
		self.__connection.commit()
		self.__getMapListFromServer()
		
		self.callMethod(('Karma', 'addType'), self.__MapObjectType)
		
		self.callMethod(('Acl', 'rightAdd'), 'Maps.addFromMX', 'Add maps from mania-exchange')
		self.callMethod(('TmChat', 'registerChatCommand'), 'addmx', ('Maps', 'chat_addmx'), 
						'Add a map from mania-exchange')
		
		self.callMethod(('TmChat', 'registerChatCommand'), 'list', ('Maps', 'chat_list'), 
						'List all maps that are currently on the server')
		
		self.callMethod(('Acl', 'rightAdd'), 'Maps.removeThis', 
					'Remove (does not delete file) the current map from server')
		self.callMethod(('TmChat', 'registerChatCommand'), 'removethis', ('Maps', 'chat_removethis'), 
						'Remove the current map from the server (does not delete file)')
		
		self.callMethod(('Acl', 'rightAdd'), 'Maps.skip', 'Skip the current map')
		self.callMethod(('TmChat', 'registerChatCommand'), 'skip', ('Maps', 'chat_skip'),
					'Skip the current map')
		
		self.callMethod(('Acl', 'rightAdd'), 'Maps.restart', 'Restart the current map')
		self.callMethod(('TmChat', 'registerChatCommand'), 'restart', ('Maps', 'chat_restart'),
					'Restart the current map')
		
		self.callMethod(('Acl', 'rightAdd'), 'Maps.saveMatchSettings', 'Save matchsettings to file.')
		self.callMethod(('Acl', 'rightAdd'), 'Maps.loadMatchSettings', 'Load matchsettings from file.')
		self.callMethod(('Acl', 'rightAdd'), 'Maps.setMatchSettingsFileName', 
					'Set the current matchsettings file name.')
		self.callMethod(('Acl', 'rightAdd'), 'Maps.getMatchSettingsFileName', 
					'Get the current matchsettings file name.')
		self.callMethod(('TmChat', 'registerChatCommand'), 'matchsettings', 
					('Maps', 'chat_matchsettings'), 'Manage the matchsettings of the server.')
		
		self.callMethod(('Acl', 'rightAdd'), 'Maps.jukeboxAdd', 'Add a map to the jukebox')
		self.callMethod(('Acl', 'rightAdd'), 'Maps.jukeboxAddMultiple', 'Add multiple maps to the jukebox')
		self.callMethod(('Acl', 'rightAdd'), 'Maps.jukeboxDrop', 'Drop your juked map from the jukebox')
		self.callMethod(('Acl', 'rightAdd'), 'Maps.jukeboxDropOthers', 
					'Drop other\'s juked maps from jukebox')
		self.callMethod(('Acl', 'rightAdd'), 'Maps.jukeboxDisplay', 
					'Display the jukebox')
		self.callMethod(('TmChat', 'registerChatCommand'), 'jukebox', ('Maps', 'chat_jukebox'),
					'Jukebox mapmanagement. Type /jukebox help for more information')
		
		self.callMethod(('TmChat', 'registerChatCommand'), 'karma', ('Maps', 'chat_karma'),
					'Handle the karma of this map.')
		
		self.callMethod(('TmChat', 'registerChatCommand'), '---', ('Maps', 'chat_triple_minus'),
					'Like /karma vote 0')
		self.callMethod(('TmChat', 'registerChatCommand'), '--', ('Maps', 'chat_double_minus'),
					'Like /karma vote 17')
		self.callMethod(('TmChat', 'registerChatCommand'), '-', ('Maps', 'chat_minus'),
					'Like /karma vote 33')
		self.callMethod(('TmChat', 'registerChatCommand'), '-+', ('Maps', 'chat_plus_minus'),
					'Like /karma vote 50')
		self.callMethod(('TmChat', 'registerChatCommand'), '+-', ('Maps', 'chat_plus_minus'),
					'Like /karma vote 50')
		self.callMethod(('TmChat', 'registerChatCommand'), '+', ('Maps', 'chat_plus'),
					'Like /karma vote 67')
		self.callMethod(('TmChat', 'registerChatCommand'), '++', ('Maps', 'chat_double_plus'),
					'Like /karma vote 83')
		self.callMethod(('TmChat', 'registerChatCommand'), '+++', ('Maps', 'chat_triple_plus'),
					'Like /karma vote 100')
		self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'PlayerChat', 'onPlayerChat')
		
		self.callMethod(('Acl', 'rightAdd'), self.__addCommentRight, 
					'Add comments to a map.')
		self.callMethod(('Acl', 'rightAdd'), 'Maps.deleteOwnComments',
					'Delete own comments on maps.')
		self.callMethod(('Acl', 'rightAdd'), 'Maps.deleteOthersComments',
					'Delete others comments on maps.')
		self.callMethod(('Acl', 'rightAdd'), 'Maps.editOwnComments',
					'Edit own comments on maps.')
		self.callMethod(('Acl', 'rightAdd'), 'Maps.editOthersComments',
					'Edit others comments on maps.')
		self.callMethod(('Acl', 'rightAdd'), 'Maps.replyComment',
					'Reply to comments made on maps.')
		self.callMethod(('Acl', 'rightAdd'), 'Maps.voteComment',
					'Vote on comments made on maps.')
		
		self.callMethod(('TmChat', 'registerChatCommand'), 'map', ('Maps', 'chat_map'),
					'Commands concerning the current map. (see /map help)')
		
		self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'MapListModified', 'onMapListModified')
		self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'BeginMap', 'onBeginMap')
		self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'PlayerDisconnect', 'onPlayerDisconnect')
		
	def __getCursor(self):
		"""
		\brief A helper function that returns a dict cursor to the MySQLdb
		\return The dict cursor
		"""
		try:
			self.__connection.ping()
		except MySQLdb.OperationalError:
			self.connection = MySQLdb.connect(user = self.__args['user'], 
											passwd = self.__args['password'], 
											db = self.__args['db'])
		return self.__connection.cursor(MySQLdb.cursors.DictCursor)
	
	def __getMapListFromServer(self):
		"""
		\brief Retrieve the servers list of maps and save into local storage
		"""
		self.__currentMaps = self.callFunction(('TmConnector', 'GetMapList'), 10000, 0)
		self.__currentMap = self.__currentMaps[self.callFunction(('TmConnector', 'GetCurrentMapIndex'))]
		self.__nextMap = self.__currentMaps[self.callFunction(('TmConnector', 'GetNextMapIndex'))]
		
		dbInsertMaps = [(str(mapDict['UId']), 
						str(mapDict['Name']), 
						str(mapDict['Author']), 
						str(mapDict['Environnement']))
						for mapDict in self.__currentMaps]
		
		cursor = self.__getCursor()
		cursor.executemany("""
			INSERT IGNORE INTO `maps` 
			(`Uid`, `Name`, `Author`, `Environment`) 
			VALUES (%s, %s, %s, %s);""",
			dbInsertMaps) 
		cursor.close()
		self.__connection.commit()
		
	def __getMapPath(self):
		"""
		\brief Get the path under which the servers maps are stored
		"""
		path = self.callFunction(('TmConnector', 'GetMapsDirectory'))
			
		if not path[-1] == os.path.sep:
			path += os.path.sep
			
		return path
	
	def getMap(self, mapId):
		"""
		\brief Get the database information of the map with the given id
		\param mapId The id of the map to fetch
		\return The database row or none if invalid id
		"""
		cursor = self.__getCursor()
		cursor.execute(
		'''
		SELECT *
		FROM maps
		WHERE Id = %s
		''',(mapId,))
		return cursor.fetchone()
		
	def	getCurrentMap(self):
		"""
		\brief Get the dict of the map that is currently running
		\return The map dict or None if an error occured
		"""
		return self.__currentMap
	
	def getMapIdFromUid(self, uid):
		"""
		\brief Map from an uid to a mapId in database
		\param uid The uid to resolve
		"""
		cursor = self.__getCursor()
		cursor.execute("""
		SELECT `Id` FROM `maps` WHERE `Uid` = %s
		""", (uid, ))
		try:
			return cursor.fetchone()['Id']
		except KeyError:
			return None
		
	def getCurrentMapId(self):
		"""
		\brief Get the database id of the current map
		\return The id (int)
		"""
		return self.getMapIdFromUid(self.getCurrentMap()['UId'])
	
	def addMap(self, fileName, Data):
		"""
		\brief Create a new map with the given name and Data in the servers maps directory
		\param fileName The map name, can be expanded by relative paths (the directories must exist)
		\param Data The contents of the map file
		"""
		mapPath = self.__getMapPath()
		mapPath += fileName
		if not os.path.isfile(mapPath):
			mapFile = open(mapPath, "w")
			mapFile.write(Data)
			mapFile.close()
			#add the map to try if it is valid
			if self.callFunction(('TmConnector', 'AddMap'), fileName):
				#remove map to let the caller decide where and if to add it
				self.callMethod(('TmConnector', 'RemoveMap'), fileName)
				return True
			else:
				return False
		else:
			return False
			
	def addFromMX(self, mxId):
		"""
		\brief Add a new map from Maniaexchange
		\param mxId The id of the map on mania-exchange.com
		\return Mapname if the map was added and None if it was not possible
		"""	
		f = urllib.urlopen('http://tm.mania-exchange.com/tracks/download/' + str(mxId))
		content = f.read()
		f.close() 
		f = urllib.urlopen('http://tm.mania-exchange.com/api/tracks/get_track_info/id/' + str(mxId) + '?format=json')
		info = f.read()
		f.close()
		info = json.loads(info)
		#create mx path when not already existing
		if not os.path.isdir(self.__getMapPath() + self.__mxPath):
			os.mkdir(self.__getMapPath() + self.__mxPath)
		#assemble filename
		fileName = info['Name'] + '.' + str(mxId) + '.Map.Gbx'
		#add the map to the mx path
		self.addMap(self.__mxPath + fileName, content)
		return fileName
	
	def chat_addmx(self, login, params):
		"""
		\brief Chat command callback to add a map from mx
		\param args The arguments from the chat
		"""
		try:
			mxId = int(params)
		except ValueError:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'MX Ids are integers!', login)
			return
		if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.addFromMX'):
			fileName = self.addFromMX(mxId)
			self.callMethod(('TmConnector', 'AddMap'), self.__mxPath + fileName)
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'You do not have the right to add maps from mania-exchange', login)
			
	def chat_list(self, login, params):
		"""
		\brief Chat callback for the map list
		\param login The login of the caller
		\param params Additional parameters given by the caller
		
		Displays a list of all maps to the calling player
		"""
		def timeToString(time):
			sec = (time  % 60000) / 1000.0
			minutes = (time // 60000)
			return "{}:{:2.3f}".format(minutes, sec)
		rows = 	[(i + 1, 
				self.__currentMaps[i]['Name'],
				self.__currentMaps[i]['Author'],
				timeToString(self.__currentMaps[i]['GoldTime'])) 
				for i in xrange(len(self.__currentMaps))]
		#save the list for this user
		self.__playerDict[login] = dict([(i[0], self.__currentMaps[i[0] - 1]['FileName']) for i in rows])
		rows  = [(Label(str(i[0]), ('Maps', 'listCallback'), (i[0], )),
				Label(i[1], ('Maps', 'listCallback'), (i[0], )), 
				Label(i[2]), 
				Label(i[3]))
				for i in rows]
		self.callMethod(('WindowManager', 'displayTableWindow'), 
					login, 'Maps.Maplist', 'Maplist', (70, 60), (-35, 30), rows, 15, (5, 30, 25, 10),
					('Id', 'Mapname', 'Authorname', 'GoldTime'))
	
	def listCallback(self, entries, login, mapId):
		if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.jukeboxAddMultiple'):
			self.chat_list(login, None)
		else:
			self.callMethod(('WindowManager', 'closeWindow'), {}, login, 'Maps.Maplist')
						
		self.chat_jukebox(login, 'add ' + str(mapId))
	
	def onMapListModified(self, CurMapIndex, NextMapIndex, isListModified):
		"""
		\brief Callback when the maplist was modified
		\param CurMapIndex The index of the current map in the maplist
		\param NextMapIndex The index of the next map in the maplist
		\param isListModified Denotes if the list was modified or if only the curmap/nextmap indices changed
		"""
		if isListModified:
			self.__getMapListFromServer()
		self.__currentMap = self.__currentMaps[CurMapIndex]
		self.__nextMap = self.__currentMaps[NextMapIndex]
			
	def chat_removethis(self, login, params):
		"""
		\brief Chat callback to remove the current map from server
		\param login The login of the player
		\param params Additional parameters that were given by the player
		\return True when the map is no longer in map list, False if could not remove
		"""
		if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.removeThis'):
			if self.callFunction(('TmConnector', 'RemoveMap'), self.getCurrentMap()['FileName']):
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'Current map (' + self.getCurrentMap()['Name'] + ') removed (did not delete file)!', login)
				return True
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'Could not remove current map, try again later!', login)
				return False
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'You do not have the right to remove the current map from the server!', login)
			return False
		
	def chat_matchsettings(self, login, param):
		"""
		\brief Handle matchsettings 
		\param login The calling login
		\param param Additional param on what to do
		
		save - Save the current matchsettings to file
		load - Load the current matchsettings from file
		display - Show the current matchsettings 
		"""
		if isinstance(param, str):
			params = param.split()
		else:
			params = []
			
		subcommands = {'help'		: 'Display the help ("... help <command>" for details).',
						'save'		: 'Save the matchsettings file from current settings.',
						'load'		: 'Load current settings from matchsettings file.',
						'set'		: 'Set the matchsettings filename.',
						'get'		: 'Get the matchsettings filename.'
						#'display'	: 'Display the current matchsettings.'
						}
		if len(params) == 0 or params[0] == 'help':
			if len(params) > 1:
				try:
					text = subcommands[params[1]]
				except KeyError:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Unknown command "'+ params[1] +'"', login)
					return None
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'matchsettings ' + params[1] + ': ' + text, login)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'matchsettings sub commands: ' + ', '.join(subcommands.keys()), login)
		elif params[0] == 'save':
			if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.saveMatchSettings'):
				self.callMethod(('TmConnector', 'SaveMatchSettings'), 
							'MatchSettings' + os.path.sep + self.__matchSettingsFileName)
				self.log('Matchsettings saved to file ' + self.__matchSettingsFileName + ' by ' + login)
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'Saved matchsettings to ' +	self.__matchSettingsFileName, login)
			else:
				self.log(login + ' had insufficient rights to save matchsettings')
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'You have insufficient rights to save matchsettings to file!', login)
		elif params[0] == 'load':
			if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.loadMatchSettings'):
				self.callMethod(('TmConnector', 'LoadMatchSettings'), 
							'MatchSettings' + os.path.sep + self.__matchSettingsFileName)
				self.log('Matchsettings loaded from file ' + self.__matchSettingsFileName + ' by ' + login)
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'Loaded matchsettings from ' + self.__matchSettingsFileName, login)
			else:
				self.log(login + ' had insufficient rights to save matchsettings')
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'You have insufficient rights to load matchsettings from file!', login)
		#elif params[0] == 'display':
		#	pass
		elif params[0] == 'set':
			if len(params) > 1:
				if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.setMatchSettingsFileName'):
					self.__matchSettingsFileName = params[1]
					self.log(login + ' changed match settings file name to ' 
							+ self.__matchSettingsFileName)
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Changed matchsettings file name to ' + self.__matchSettingsFileName, 
								login)
				else:
					self.log(login + ' has insufficient rights to change match settings file name!')
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'You have insufficient rights to change the match settings file name!',
								login)
		elif params[0] == 'get':
			if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.getMatchSettingsFileName'):
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Matchsettings filename is: ' + self.__matchSettingsFileName, 
								login)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'You have insufficient rights to view the matchsettings filename!', 
								login)
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'Unknown command \'matchsettings ' + param + '\'', login)
			
	def chat_skip(self, login, params):
		"""
		\brief Skip current map
		\param login The calling login
		\param params Additional parameters
		"""
		if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.skip'):
			if self.callFunction(('TmConnector', 'NextMap')):
				self.callMethod(('TmConnector', 'ChatSendServerMessage'),
							self.callFunction(('Players', 'getPlayerNickname'), login)
							+ ' $zskipped map.')
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'Could not skip map, try again later!', login)
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'You are not allowed to skip maps', login)
			
	def chat_restart(self, login, params):
		"""
		\brief Restart current map
		\param login The calling login
		\param params Additional parameters
		"""
		if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.restart'):
			if self.callFunction(('TmConnector', 'RestartMap')):
				self.callMethod(('TmConnector', 'ChatSendServerMessage'),
							self.callFunction(('Players', 'getPlayerNickname'), login)
							+ ' $z$g restarted map.')
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'Could not restart map, try again later!', login)
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'You are not allowed to restart maps', login)
			
	def onBeginMap(self, Map, isWarmUp, isMatchContinuation):
		"""
		\brief Callback on begin of map
		\param Map A struct containing information about the current map
		\param isWarmup Is this warmupMode?
		\param isMatchContinuation Is this a continuation of the map?
		
		Used to remove maps from jukebox when they are played
		"""
		if (len(self.__jukebox) > 0 and 
			self.__jukebox[0][0]['FileName'] == Map['FileName']):
			self.__jukebox.pop(0) 
			
	def chat_jukebox(self, login, params):
		"""
		\brief Jukebox management
		\param login The login of the calling player
		\param params Additional params given by the player
		
		add <id> - add a map to the jukebox
		drop <id> - drop a map from jukebox
		"""
		if isinstance(params, str):
			params = params.split()
		else:
			params = ['display']
		
		if params[0] == 'help':
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'This method is a stub, inform the programmer to implement it!', login)
		if len(params) > 1 and params[0] == 'add':
			if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.jukeboxAdd'):
				try:
					newJukeboxEntry = self.__playerDict[login][int(params[1])]
				except KeyError:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Could not find the map with id ' + str(params[1]), login)
					return False
				except ValueError:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Mapindices have to be integer numbers!', login)
					return False
				
				if len(filter(lambda x: (x[0]['FileName'] == newJukeboxEntry), self.__jukebox)) > 0:
					self.callFunction(('TmConnector', 'ChatSendServerMessageToLogin'), 
									'This map is already in jukebox, wait until it is being played!',
									login)
					return False
				
				if (len(filter(lambda x: (login == x[1]),self.__jukebox)) > 0 and 
					not self.callFunction(('Acl', 'userHasRight'), login, 'Maps.jukeboxAddMultiple')):
						self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'''You already have a newJukeboxEntry in jukebox, wait until it has been played or
								drop it to add this one.''', login)
						return False
				
				#now we know that the map will be juked we need to find it in the list
				newJukeboxEntry = filter(lambda x: x['FileName'] == newJukeboxEntry,
										self.__currentMaps)[0]
					
				self.__jukebox.append((newJukeboxEntry, login))
				self.callMethod(('TmConnector', 'ChatSendServerMessage'), 
							self.callFunction(('Players', 'getPlayerNickname'), login)
							+ ' $zJukeboxed map ' + newJukeboxEntry['Name'])
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'You have insufficient rights to add maps to the jukebox!', login)
		elif params[0] == 'drop':
			if len(params) > 1:
				try:
					index = int(params[1]) - 1
				except ValueError:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Indices have to be integer numbers!', login)
					return False
			else:
				myMaps = filter(lambda x: (login == x[1]), self.__jukebox)
				if len(myMaps) == 0:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'You do not have any maps in jukebox!', login)
				else:
					index = self.__jukebox.index(myMaps[0])
					
			try:
					newJukeboxEntry = self.__jukebox[index]
			except IndexError:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'Invalid jukebox id "' + params[1] + '"', login)
				return False		
					
					
			if newJukeboxEntry[1] == login:
				if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.jukeboxDrop'):
					self.__jukebox.pop(self.__jukebox.index(newJukeboxEntry))
					self.callMethod(('TmConnector', 'ChatSendServerMessage'), 
								self.callFunction(('Players', 'getPlayerNickname'), login) + 
								' $z removed map ' + newJukeboxEntry[0]['Name'] + ' $zfrom jukebox.')
				else:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'You have insufficient rights to drop your newJukeboxEntry from jukebox!', login)
			else:	
				if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.jukeboxDropOthers'):
					self.__jukebox.pop(self.__jukebox.index(newJukeboxEntry))
					self.callMethod(('TmConnector', 'ChatSendServerMessage'), 
								self.callFunction(('Players', 'getPlayerNickname'), login) + 
								' $z removed map ' + newJukeboxEntry[0]['Name'] + ' $zfrom jukebox.')
				else:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'You have insufficient rights to drop other\'s newJukeboxEntry from jukebox!', login)
		elif params[0] == 'display':
			if len(self.__jukebox) == 0:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'The jukebox is empty', login)
				#hide jukebox when empty
				self.callMethod(('WindowManager', 'closeWindow'), {}, login, 'Maps.Jukebox')
				return False
			rows = []
			for i in xrange(len(self.__jukebox)):
				t = self.__jukebox[i]
				rows.append((
								Label(i + 1, ('Maps', 'jukeboxCallback'), (i + 1,)),
								Label(t[0]['Name'], ('Maps', 'jukeboxCallback'), (i + 1,)), 
								Label(self.callFunction(('Players', 'getPlayerNickname'), t[1]))
							))
			self.callMethod(('WindowManager', 'displayTableWindow'),
					login, 'Maps.Jukebox', 'Jukebox', (80, 40), (-40, 20), rows, 10, (5, 45, 30),
					('Id', 'Map Name', 'Player'))
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'Unknown command \'/jukebox ' + ' '.join(params) + '\'', login)
			
		self.callMethod(('TmConnector', 'ChooseNextMapList'), 
					[i[0]['FileName'] for i in self.__jukebox])
	
	def jukeboxCallback(self, entries, login, mapId):
		"""
		\brief Called when user clicks element in list command
		\param entries The entries of the manialink (should be empty)
		\param login The login of the calling player 
		\param mapId The id of the map in the users list of maps  
		"""
		self.chat_jukebox(login, 'drop ' + str(mapId))
		if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.jukeboxAddMultiple'):
			self.chat_jukebox(login, 'display')
		else:
			self.callMethod(('WindowManager', 'closeWindow'), {}, login, 'Maps.Jukebox')
			
	def onPlayerDisconnect(self, login):
		"""
		\brief Called on disconnection of users
		\param login The login of the disconnecting user
		
		Used to free the memory that this users data occupied
		"""
		try:
			del self.__playerDict[login]
		except KeyError:
			#only raised when this player never used the jukebox
			pass
		
	def chat_karma(self, login, params):
		"""
		\brief Handle the karma commands for the current map
		\param login
		\param params
		"""
		#default action is showing the karma
		if params == None:
			params = 'show'
			
		params = params.split()
		
		currentMapId = self.getMapIdFromUid(self.getCurrentMap()['UId'])
		
		if params[0] == 'show':
			votes = self.callFunction(('Karma', 'getVotes'), 
									self.__MapObjectType, 
									currentMapId)
			karma = self.callFunction(('Karma', 'getKarma'), 
									self.__MapObjectType,
									currentMapId)
			positiveCount = len(filter(lambda x: x[0] >= 50,votes))
			negativeCount = len(filter(lambda x: x[0] < 50,votes))
			totalCount = positiveCount + negativeCount
			if totalCount > 0:
				positivePercent = 100 * positiveCount // totalCount
				negativePercent = 100 * negativeCount // totalCount
			else:
				positivePercent = 0
				negativePercent = 0
			try:
				karma = int(karma)
			except TypeError:
				karma = 0
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'Current Karma {}: $1f1++{}({}%) $f11-- {}({}%)'.format(
							karma, positiveCount, positivePercent, negativeCount, negativePercent)
						,login)
		elif params[0] == 'vote':
			try:
				vote = int(params[1])
			except ValueError:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'/karma vote expects parameter to be integer.' , login)
				return False
			except IndexError:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'/karma vote expects an integer within the range 0 - 100 as vote.', 
						login)
				return False
			
			if vote < 0:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'Your vote has to be at least 0, so I clamped it to 0.', login)
				vote = 0
			elif vote > 100:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'Your vote can at most be 100, so I clamped it to 100.', login)
				vote = 100
			
			self.callMethod(('Karma', 'changeVote'), 
						self.__MapObjectType, currentMapId, vote, login)
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'Accepted your vote of ' + str(vote), login)
			self.chat_karma(login, 'show')			
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'Unknown command /karma ' + ' '.join(params), login)
			
	def chat_triple_minus(self, login, params):
		"""
		\brief Convenience function for /karma vote 0
		"""
		self.chat_karma(login, 'vote 0')
	
	def chat_double_minus(self, login, params):
		"""
		\brief Convenience function for /karma vote 17
		"""
		self.chat_karma(login, 'vote 17')
		
	def chat_minus(self, login, params):
		"""
		\brief Convenience function for /karma vote 33
		"""
		self.chat_karma(login, 'vote 33')
		
	def chat_plus_minus(self, login, params):
		"""
		\brief Convenience function for /karma vote 50
		"""
		self.chat_karma(login, 'vote 50')
		
	def chat_plus(self, login, params):
		"""
		\brief Convenience function for /karma vote 67
		"""
		self.chat_karma(login, 'vote 67')
	
	def chat_double_plus(self, login, params):
		"""
		\brief Convenience function for /karma vote 83
		"""
		self.chat_karma(login, 'vote 83')
		
	def chat_triple_plus(self, login, params):
		"""
		\brief Convenience function for /karma vote 100
		"""
		self.chat_karma(login, 'vote 100')	
		
	def onPlayerChat(self, PlayerUid, Login, Text, IsRegisteredCmd):
		"""
		\brief Player chat callback
		
		Filters chat for convenience chat votes ---, --, -, +-, -+, +, ++, ++
		"""
		Text = Text.strip()
		functions = {'---' : self.chat_triple_minus,
					'--' : self.chat_double_minus,
					'-' : self.chat_minus,
					'+-' : self.chat_plus_minus,
					'-+' : self.chat_plus_minus,
					'+' : self.chat_plus,
					'++' : self.chat_double_plus,
					'+++' : self.chat_triple_plus}
		try:
			functions[Text](Login, None)
		except KeyError:
			pass
		
	def chat_map(self, login, params):
		"""
		\brief Handle chat commands concerning the current map
		\param login The login of the calling player
		\param params Additional params
		"""
		if params == None:
			params = 'help'
			
		params = params.split()
			
		commands = {
				'help' : 'Display all subcommand names of map.',
				'comment' : 'Write a comment about this map.',
				'comments' : 'Display all comments about this map'
				}
		
		if params[0] == 'help':
			if len(params) == 2:
				try:
					description = commands[params[1]]
				except KeyError:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Could not find help for ' + params[1], login)
					return None
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'command /map ' + params[1] + ': ' + description, login)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'command /map has following subcommands: ' + str(commands.keys())
						+ ' try /map help <subcommand> to for more information', 
						login)
				
		elif params[0] == 'comment':
			try:
				self.chat_comment(login, ' '.join(params[1:]))
			except IndexError:
				self.chat_comment(login, None)
		elif params[0] == 'comments':
			self.chat_comment(login, 'display')
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'Unknown command /map ' + str(' '.join(params)), login)
		
	def chat_comment(self, login, params, preserveState = False):
		"""
		\brief The comment chatcommand callback
		\param login The calling players login
		\param params additional params to the command
		"""
		if params == None:
			params = 'write'
			
		params = params.split()
		
		mapId = self.getMapIdFromUid(self.getCurrentMap()['UId'])
		if len(params) > 1:
			try:
				mapId = int(params[1])
			except:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'A mapId is an integer!', login)
			
		mapDict = self.getMap(mapId)
		
		if params[0] == 'write':
			commentWindow = CommentInput(('Maps', 'cb_comment'), (),
										'Comment on ' + mapDict['Name'])
			commentWindow.setSize((70, 50))
			commentWindow.setPos((-30, 25))
			self.callMethod(('WindowManager', 'displayWindow'), 
						login, self.__writeCommentWindowName, 
						commentWindow)
		elif params[0] == 'display':
			comments = self.callFunction(('Karma', 'getComments'), 
										self.__MapObjectType, 
										mapId)
			if len(comments) == 0:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'There are no comments on this map.', login)
				return
			comments = self.__prepareComments(comments, login)
			commentsWindow = CommentOutput(str(len(comments)) + ' Comments on '
										 + mapDict['Name'])
			commentsWindow.setSize((80, 70))
			commentsWindow.setPos((-40, 35))
			commentsWindow.setCommentAnswerCallback(('Maps', 'cb_commentAnswer'))
			commentsWindow.setCommentDeleteCallback(('Maps', 'cb_commentDelete'))
			commentsWindow.setCommentEditCallback(('Maps', 'cb_commentEdit'))
			commentsWindow.setCommentVoteCallback(('Maps', 'cb_commentVote'))
			commentsWindow.setComments(comments)
			self.callMethod(('WindowManager', 'displayWindow'), 
						login, self.__displayCommentsWindowName, 
						commentsWindow, preserveState)
	
	def __prepareComments(self, comments, login, depth = 0):
		canDeleteOwn = self.callFunction(('Acl', 'userHasRight'), login, 'Maps.deleteOwnComments')
		canDeleteOthers = self.callFunction(('Acl', 'userHasRight'), login, 'Maps.deleteOthersComments')
		canEditOwn = self.callFunction(('Acl', 'userHasRight'), login, 'Maps.editOwnComments')
		canEditOthers = self.callFunction(('Acl', 'userHasRight'), login, 'Maps.editOthersComments')
		canReply = self.callFunction(('Acl', 'userHasRight'), login, 'Maps.replyComment')
		canVote = self.callFunction(('Acl', 'userHasRight'), login, 'Maps.voteComment')
		output = []
		for i in comments:
			if i[2] == login:
				#the comment is mine
				votable = False #Can not vote on own comment
				editable = canEditOwn
				deletable = canDeleteOwn
				answerable = False #Can not answer own comment
			else:
				#the comment is from someone else
				votable = canVote
				editable = canEditOthers
				deletable = canDeleteOthers
				answerable = canReply
				
			comment = {'depth' : depth, 
						'height' : 4, 
						'karma' : reduce(lambda x, y: x + y[0], i[4], 0),
						'votable' : votable,
						'editable' : editable,
						'deletable' : deletable,
						'answerable' : answerable,
						'nickName' : self.callFunction(('Players', 'getPlayerNickname'), i[2]),
						'commentTuple' : i}
			#append the answers to this comment
			output.extend(self.__prepareComments(i[5], login, depth + 1))
			#append this comment
			output.append(comment)
		return output
	
	def cb_commentDelete(self, entries, login, commentId):
		"""
		\brief Delete a comment
		\param entries Should be emtpy
		\param login The login of the invoking player
		\param commentId The id of the comment to delete
		"""
		comment = self.callFunction(('Karma', 'getComment'), commentId)
		if comment[2] == login:
			#it is my comment
			if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.deleteOwnComments'):
				self.callMethod(('Karma', 'deleteComment'), commentId)
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'Deleted your comment.', login)
				#Refresh the comments window
				self.chat_comment(login, 'display', True)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'You are not allowed to delete your comments.', login)
		else:
			#it is someone else comment
			if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.deleteOthersComments'):
				self.callMethod(('Karma', 'deleteComment'), commentId)
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'$zDeleted ' + 
							self.callFunction(('Players', 'getPlayerNickname'), 
											comment[2]) + 
							' $zcomment.', login)
				#Refresh the comments window
				self.chat_comment(login, 'display', True)
			else:
				self.log('Error: User ' + login + ' tried to delete ' + 
						comment[2] + '\'s comment')
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'You are not allowed to delete others comments!', login)
				
	def cb_commentEdit(self, entries, login, commentId):
		"""
		\brief Callback for editing a comment
		\param entries Should be empty
		\param login The login of the invoking player
		\param commentId The id of the comment to edit
		"""
		#Hide the comment window
		self.callMethod(('WindowManager', 'closeWindow'), {}, login, 
					self.__displayCommentsWindowName)
		comment = self.callFunction(('Karma', 'getComment'), commentId)
		
		if comment[2] == login:
			#it is my comment
			if self.callFunction(('Acl', 'userHasRight'), 
								login, self.__editOwnCommentsRight):
				pass
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'You are not allowed to edit your comments.', login)
				return	
		else:
			#it is someone else comment
			if self.callFunction(('Acl', 'userHasRight'), 
								login, self.__editOthersCommentsRight):
				pass
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'You are not allowed to edit others comments.', login)
				return
			
		commentWindow = CommentInput(('Maps', 'cb_commentChanged'), (commentId, ), 
										'Edit comment', comment[1])
		commentWindow.setSize((70, 50))
		commentWindow.setPos((-30, 25))
		self.callMethod(('WindowManager', 'displayWindow'), login, 
					self.__writeCommentWindowName, commentWindow)
		
	def cb_commentVote(self, entries, login, commentId, vote):
		"""
		\brief The comment vote callback
		\param entries Should be empty
		\param login The login of the invoking player
		\param commentId The id of the comment to vote on
		\param vote The vote value
		"""
		if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.voteComment'):
			comment = self.callFunction(('Karma', 'getComment'), commentId)
			if comment[2] == login:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'You are not allowed to vote for your own comments', login)
				return
			else:				
				self.callMethod(('Karma', 'changeVote'), 
							self.callFunction(('Karma', 'getCommentTypeName')),
							commentId, 
							vote,
							login)
				
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'Thank you for voting.', login)
				#Refresh the comments window
				self.chat_comment(login, 'display', True)
			
	def cb_comment(self, entries, login):
		self.callMethod(('WindowManager', 'closeWindow'), {}, login, self.__writeCommentWindowName)
		
		if self.callFunction(('Acl', 'userHasRight'), login, 
									self.__addCommentRight):
			self.callMethod(('Karma', 'addComment'), self.__MapObjectType, 
				self.getMapIdFromUid(self.getCurrentMap()['UId']),
				entries['commentText'], login) 
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'Thank you for you opinion.', login)
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'You have insufficient rights to add comments to a map', login)
			
	def cb_commentChanged(self, entries, login, commentId):
		self.callMethod(('WindowManager', 'closeWindow'), {}, login, self.__writeCommentWindowName)
		
		comment = self.callFunction(('Karma', 'getComment'), commentId)
		
		if comment[2] == login:
			#it is my comment
			if self.callFunction(('Acl', 'userHasRight'), login,
							self.__editOwnCommentsRight):
				self.callMethod(('Karma', 'editComment'), commentId, 
							entries['commentText'])
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'Comment edited.', login)
			else:
				self.callMethod(('TmChat', 'ChatSendServerMessageToLogin'),
							'You have insufficient rights to edit your comment.', login)
		else:
			#it is someone else' comment'
			if self.callFunction(('Acl', 'userHasRight'), login,
								self.__editOthersCommentsRight):
				self.callMethod(('Karma', 'editComment'), commentId, 
							entries['commentText'])
				self.callMethod(('TmChat', 'ChatSendServerMessageToLogin'),
							'Comment edited.', login)
			else:
				self.log(login + ' tried to edit comment of ' + comment[2] + 
						' without the right to do this')
				self.callMethod(('TmChat', 'ChatSendServerMessageToLogin'),
							'You have insufficient rights to edit comments of other players.', login)
				
	def cb_commentAnswer(self, entries, login, commentId):
		"""
		\brief Callback on clicking answer on comments
		\param entries Should be empty
		\param login The login of the calling player
		\param commentId The id of the comment to answer to
		"""
		if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.replyComment'):
			comment = self.callFunction(('Karma', 'getComment'), commentId)
			if comment[2] != login:
				self.callMethod(('WindowManager', 'closeWindow'), {}, login, 
							self.__displayCommentsWindowName)
				nickName = self.callFunction(('Players', 'getPlayerNickname'), comment[2])
				
				commentWindow = CommentInput(('Maps', 'cb_commentAnswered'), (commentId, ), 
											'Answer to ' + str(nickName) + ' $z\'s comment', 
											'Type your answer here (double click to edit)')
				commentWindow.setSize((70, 50))
				commentWindow.setPos((-30, 25))
				self.callMethod(('WindowManager', 'displayWindow'), login, 
							self.__writeCommentWindowName, commentWindow)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'You are not allowed to answer your own comments.', 
						login)
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'You have insufficient rights to reply to comments.', 
						login)
		
	def cb_commentAnswered(self, entries, login, commentId):
		"""
		\brief Callback on clicking answer on comments
		\param entries Should be empty
		\param login The login of the calling player
		\param commentId The id of the comment to answer to
		"""
		self.callMethod(('WindowManager', 'closeWindow'), {}, login, 
					self.__writeCommentWindowName)
		if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.replyComment'):
			comment = self.callFunction(('Karma', 'getComment'), commentId)
			if comment[2] != login:
				nickName = self.callFunction(('Players', 'getPlayerNickname'), comment[2])
				self.callMethod(('Karma', 'addComment'), 
							self.callFunction(('Karma', 'getCommentTypeName')),
							commentId,
							entries['commentText'],
							login)
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'Thank you for your answer to ' + nickName + '$z\'s comment', 
						login)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'You are not allowed to answer your own comments.', 
						login)
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'You have insufficient rights to reply to comments.', 
						login)