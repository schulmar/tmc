from PluginInterface import *
import MySQLdb
import time

class Players(PluginInterface):
	def __init__(self, pipes, args):
		self.playerList = {}
		super(Players, self).__init__(pipes)

	def initialize(self, args):
		self.connection = MySQLdb.connect(user = args['user'], passwd = args['password'], db = args['db'])
		self.__checkTables()
		self.__loadCurrentPlayers()
		self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'PlayerConnect', 'onPlayerConnect') 
		self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'EndMap', 'onEndMap')
		self.callMethod(('TmChat', 'registerChatCommand'), 'players', ('Players', 'chat_players'), 'Commands concerning players. Type /players help to see available commands')

	def __getCursor(self):
		return self.connection.cursor(MySQLdb.cursors.DictCursor)

	def __checkTables(self):
		cursor = self.__getCursor()
		cursor.execute('SHOW COLUMNS FROM `users`')		
		columns = [c['Field'] for c in cursor.fetchall()]
		self.log('Checking integrity of database...')
		if not 'nick' in columns:
			self.log('Adding column `nick` to table `users`')
			cursor.execute('ALTER TABLE `users` ADD `nick` text')
		if not 'lastOnline' in columns:
			self.log('Adding column `UpdatedAt` to table `users`')
			cursor.execute('ALTER TABLE `users` ADD `UpdatedAt` datetime')
		self.log('... database integrity check completed')
		cursor.close()
		self.connection.commit()

	def __loadCurrentPlayers(self):
		result = self.callFunction(('TmConnector', 'GetPlayerList'), 1000, 0)
		for player in result:
			self.callFunction(('Acl', 'userAdd'), player['Login'])
			self.onPlayerConnect(player['Login'], False)

	def onPlayerConnect(self, login, IsSpectator):	
		self.callFunction(('Acl', 'userAdd'), login)
		info = self.callFunction(('TmConnector', 'GetDetailedPlayerInfo'), login)
		cursor = self.__getCursor()
		cursor.execute('UPDATE `users` SET `nick`=%s WHERE `name`=%s', (info['NickName'], login) )
		groups = self.callFunction(('Acl', 'userGetGroups'), login)
		if len(groups) == 0:
			message = '$zNew Player: '
		else:
			message = groups[0] + ': '

		message += info['NickName']
		message += '$1E1 Country$z: ' + str(info['Path'].split('|')[1])
		message += '$1E1 Ladder$z: ' + str(info['LadderStats']['PlayerRankings'][0]['Ranking'])
		self.callMethod(('TmConnector', 'ChatSendServerMessage'), message)
		self.__gatherPlayerInformation

	def __gatherPlayerInformation(self, playerName):
		self.playerList[playerName] = {}
		info = self.callFunction(('TmConnector', 'getDetailedPlayerInfo'), playerName)
		self.playerList[playerName] = info


	def onEndMap(self, Rankings, Map, WasWarmUp, MatchContinuesOnNextMap, restartMap):
		if (not WasWarmUp):
			cursor = self.__getCursor()
			for rank in Rankings:
				if rank['BestTime'] != -1:
					cursor.execute('UPDATE `users` SET `updatedAt`=NOW() WHERE `name`=%s', (rank['Login'], ))

	def chat_players(self, login, args):
		"""
		\brief Commandos regarding all players
		\param login The callers login
		\param args Additional parameters to identify the operation
		
		None/List - list all players that are currently online
		"""
		if args == None or args == 'list':
			rows = [(value['NickName'], key) for (key, value) in self.playerList.items()]
			self.callMethod(('WindowManager', 'displayTableStringsWindow'), 
						login, 'Players.playerList', 'List of players that are currently on the server', 
						(30, 60), (-15, 15), rows, 15, (20, 10), ('Nickname', 'Login'))
			

	def getPlayerNickname(self, playerName):
		"""
		\brief Get the nickname of the given playerlogin
		\param playerName The login of the player
		\return The nickname, if the player is known or None if not
		"""
		if playerName in self.playerList:
			return self.playerList[playerName]['NickName']
		else:
			cursor = self.__getCursor()
			cursor.execute("SELECT `nick` FROM `users` WHERE name=%s", (playerName,))
			row = cursor.fetchone()
			if row != None:
				return row['nick']
			else:
				return None
