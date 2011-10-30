from PluginInterface import *
import MySQLdb
import os
import urllib
import json


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
		cursor = self.__getCursor()
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
		
		self.callMethod(('Acl', 'rightAdd'), 'Maps.removeThis', 'Remove (does not delete file) the current map from server')
		self.callMethod(('TmChat', 'registerChatCommand'), 'removethis', ('Maps', 'chat_removethis'), 
						'Remove the current map from the server (does not delete file)')
		
		self.callMethod(('Acl', 'rightAdd'), 'Maps.skip', 'Skip the current track')
		self.callMethod(('TmChat', 'registerChatCommand'), 'skip', ('Maps', 'chat_skip'),
					'Skip the current map')
		
		self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'MapListModified', 'onMapListModified')
		
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
		rows  = [(mapDict['Name'], mapDict['Author'], mapDict['GoldTime']) for mapDict in self.__currentMaps]
		self.callMethod(('WindowManager', 'displayTableStringsWindow'), 
					login, 'Maps.Maplist', 'Maplist', (70, 60), (-35, 30), rows, 15, (35, 25, 10),
					('Mapname', 'Authorname', 'GoldTime'))
	
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
		
	def chat_matchsettings(self, login, params):
		"""
		\brief Handle matchsettings 
		\param login The calling login
		\param params Additional params on what to do
		
		write - Write the current matchsettings to file
		read - Read the current matchsettings from file
		display - Show the current matchsettings 
		"""
		if params == 'write':
			pass
		elif params == 'read':
			pass
		elif params == 'display':
			pass
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'Unknown command \'matchsettings' + params + '\'', login)
			
	def chat_skip(self, login, params):
		"""
		\brief Skip current map
		\param login The calling login
		\param params Additional parameters
		"""
		if self.callFunction(('Acl', 'userHasRight'), login, 'Maps.skip'):
			if self.callFunction(('TmConnector', 'NextMap')):
				self.callMethod(('TmConnector', 'ChatSendServerMessage'),
							' skipped map.')
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'Could not skip map, try again later!', login)
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'You are not allowed to skip maps', login)