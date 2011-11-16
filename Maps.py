from PluginInterface import *
import MySQLdb
import os
import urllib
import json
from Manialink import *

"""
\file Maps.py
\brief Contains the Maps plugin

This plugin should manage the maps on the server
"""

class Maps(PluginInterface):
	"""
	\brief The Maps plugin class derived from PluginInterface
	"""
	__currentMaps = []#List of the maps that currently run on the server
	__currentMap = 0#The index of the current map in the list
	__nextMap = 0#The index of the next map in the list
	__mxPath = 'mania-exchange/'#The name of the folder into which mania-exchange maps will be downloaded
	__connection = None#The database connection
	__matchSettingsFileName = 'tracklist.txt'#The name of the matchsettings file
	__jukebox = []#List of tracks that are currently in the jukebox (track, loginOfJuker)
	__playerDict = {}#a dictionary that contains the index mapping of the tracks per user
	
	
	def __init__(self, pipes, args):
		"""
		\brief Construct the class
		\param pipes The pipes to the PluginManager process
		\param args Additional userdefined args 
		"""
		super(Maps, self).__init__(pipes)

	def initialize(self, args):
		"""
		\brief Initialize the plugin on startup
		\params args The user parameters for the plugin
		
		Setup the database connection create tables if necessary...
		""" 
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
		
		self.callMethod(('Acl', 'rightAdd'), 'Maps.addFromMX', 'Add maps from mania-exchange')
		self.callMethod(('TmChat', 'registerChatCommand'), 'addmx', ('Maps', 'chat_addmx'), 
						'Add a map from mania-exchange')
		
		self.callMethod(('TmChat', 'registerChatCommand'), 'list', ('Maps', 'chat_list'), 
						'List all maps that are currently on the server')
		
		self.callMethod(('Acl', 'rightAdd'), 'Maps.removeThis', 
					'Remove (does not delete file) the current map from server')
		self.callMethod(('TmChat', 'registerChatCommand'), 'removethis', ('Maps', 'chat_removethis'), 
						'Remove the current map from the server (does not delete file)')
		
		self.callMethod(('Acl', 'rightAdd'), 'Maps.skip', 'Skip the current track')
		self.callMethod(('TmChat', 'registerChatCommand'), 'skip', ('Maps', 'chat_skip'),
					'Skip the current map')
		
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
					'Jukebox trackmanagement. Type /jukebox help for more information')
		
		self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'MapListModified', 'onMapListModified')
		self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'BeginMap', 'onBeginMap')
		self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'PlayerDisconnect', 'onPlayerDisconnect')
		
	def __getCursor(self):
		"""
		\brief A helper function that returns a dict cursor to the MySQLdb
		\return The dict cursor
		"""
		return self.__connection.cursor(MySQLdb.cursors.DictCursor)
	
	def __getMapListFromServer(self):
		"""
		\brief Retrieve the servers list of maps and save into local storage
		"""
		self.__currentMaps = self.callFunction(('TmConnector', 'GetMapList'), 10000, 0)
		
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
		
	def	getCurrentMap(self):
		"""
		\brief Get the dict of the map that is currently running
		\return The map dict or None if an error occured
		"""
		try:
			return self.__currentMaps[self.__currentMap]
		except KeyError:
			return None
	
	def addMap(self, fileName, Data):
		"""
		\brief Create a new track with the given name and Data in the servers maps directory
		\param fileName The track name, can be expanded by relative paths (the directories must exist)
		\param Data The contents of the track file
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
		\brief Add a new track from Maniaexchange
		\param mxId The id of the track on mania-exchange.com
		\return Trackname if the track was added and None if it was not possible
		"""	
		f = urllib.urlopen('http://tm.mania-exchange.com/tracks/download/' + str(mxId))
		content = f.read()
		f.close() 
		f = urllib.urlopen('http://tm.mania-exchange.com//api/tracks/get_track_info/id/' + str(mxId) + '?format=json')
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
						'You do not have the right to add tracks from mania-exchange', login)
			
	def chat_list(self, login, params):
		"""
		\brief Chat callback for the map list
		\param login The login of the caller
		\param params Additional parameters given by the caller
		
		Displays a list of all tracks to the calling player
		"""
		def timeToString(time):
			sec = (time  % 60000) / 1000.0
			minutes = (time // 60000)
			return "{}:{:2.3f}".format(minutes, sec)
		rows = 	[(i, 
				self.__currentMaps[i]['Name'],
				self.__currentMaps[i]['Author'],
				timeToString(self.__currentMaps[i]['GoldTime'])) 
				for i in xrange(len(self.__currentMaps))]
		#save the list for this user
		self.__playerDict[login] = dict([(i[0], self.__currentMaps[i[0]]['FileName']) for i in rows])
		rows  = [(Label(str(i[0] + 1), ('Maps', 'listCallback'), (i[0], )),
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
		self.__currentMap = CurMapIndex
		self.__nextMap = NextMapIndex
		if isListModified:
			self.__getMapListFromServer()
			
	def chat_removethis(self, login, params):
		"""
		\brief Chat callback to remove the current map from server
		\param login The login of the player
		\param params Additional parameters that were given by the player
		\return True when the track is no longer in map list, False if could not remove
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
			
	def onBeginMap(self, Map, isWarmUp, isMatchContinuation):
		"""
		\brief Callback on begin of map
		\param Map A struct containing information about the current map
		\param isWarmup Is this warmupMode?
		\param isMatchContinuation Is this a continuation of the map?
		
		Used to remove tracks from jukebox when they are played
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
								'Could not find the newJukeboxEntry with id ' + str(params[1]), login)
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
					index = int(params[1])
				except ValueError:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Indices have to be integer numbers!', login)
					return False
			else:
				myTracks = filter(lambda x: (login == x[1]), self.__jukebox)
				if len(myTracks) == 0:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'You do not have any tracks in jukebox!', login)
				else:
					index = self.__jukebox.index(myTracks[0])
					
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
				return False
			rows = []
			for i in xrange(len(self.__jukebox)):
				t = self.__jukebox[i]
				rows.append(	(
									Label(t[0]['Name'], ('Maps', 'jukeboxCallback'), (i,)), 
									Label(self.callFunction(('Players', 'getPlayerNickname'), t[1]))
								)
							)
			self.callMethod(('WindowManager', 'displayTableWindow'),
					login, 'Maps.Jukebox', 'Jukebox', (40, 40), (-20, 20), rows, 10, (25, 15),
					('Map Name', 'Player'))
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'Unknown command \'/jukebox ' + ' '.join(params) + '\'', login)
			
		self.callMethod(('TmConnector', 'ChooseNextMapList'), 
					[i[0]['FileName'] for i in self.__jukebox])
	
	def jukeboxCallback(self, entries, login, trackId):
		"""
		\brief Called when user clicks element in list command
		\param entries The entries of the manialink (should be empty)
		\param login The login of the calling player 
		\param trackId The id of the track in the users list of tracks  
		"""
		self.chat_jukebox(login, 'drop ' + str(trackId))
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