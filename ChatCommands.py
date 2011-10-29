from PluginInterface import *



class ChatCommands(PluginInterface):
	def __init__(self, pipes, args):
		super(ChatCommands, self).__init__(pipes)
	
	def initialize(self, args):
		registerChatCommand = lambda x,y, z = '': self.callMethod(('TmChat', 'registerChatCommand'), x, ('ChatCommands', y), z)
		rightAdd = lambda x, y: self.callMethod(('Acl', 'rightAdd'), x, y)

		registerChatCommand('echo', 'chat_echo')
		registerChatCommand('listplugins', 'chat_listPlugins')
	#	registerChatCommand('restart', 'chat_restart')
		registerChatCommand('hello', 'chat_hello')

		registerChatCommand('player', 'chat_player', 'Manage one player, type /player help for more information')
		rightAdd('Player.addGroup', 'Add players to groups (that are below the calling players own highest level)')
		rightAdd('Player.removeGroup', 'Remove players from groups (that are below the calling players own highest level)')

	def chat_echo(self, login, args):
		self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), args, login)

	def chat_listPlugins(self, login, args):
		pluginNames = self.callFunction((None, 'PluginList'))
		self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), str(pluginNames), login)

	def chat_restart(self, login, args):
		self.callMethod((None, 'restartPlugin'), args)

	def chat_hello(self, login, args):
		self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'Hi there', login)

	def chat_player(self, login, args):
		print('Herer')
		if args == None:
			args = 'help'
		args = args.strip()
		args = args.split()
		commands = [('... add <player> <group>', 'Add player to a group'),
				('... remove <player> <group>', 'Remove player from a group')]
	#display help for players
		if args[0] == 'help':
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'Subcommands of /player: ' + ', '.join([i[0] for i in commands]), login)
			return True
	#add player to group
		elif args[0] == 'add':
			if len(args) != 3:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), '/player add needs exactly 2 parameters', login)
				return False

			if not self.callFunction(('Acl', 'userHasRight'), login, 'Player.addGroup'):
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'You don\'t have sufficient rights to add players to groups', login)
				return False

			userLevel = self.callFunction(('Acl', 'userGetLevel'), login)
			groupLevel = self.callFunction(('Acl', 'groupGetLevel'), args[2])

			if groupLevel > userLevel:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'You can not add players to groups that are higher than yours!', login)
				return False

			if self.callFunction(('Acl', 'userAddGroup'), args[1], args[2]):
				nick = self.callFunction(('Players', 'getPlayerNickName'), args[1])
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'Added player ' + nick + ' to group ' + args[2], login)
				return True
			else:
				self.callFunction(('TmConnector', 'ChatSendServerMessageToLogin'), 'Could not add player ' + str(args[1]) + ' to group ' + str(args[2]) + ' did you type everything correctly?', login)
				return False
	#remove player from group
		elif args[0] == 'remove':
			if len(args) != 3:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), '/player remove needs exactly 2 parameters', login)
				return False
			if not self.callFunction(('Acl', 'userHasRight'), args[1], 'Player.removeGroup'):
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'You don\'t have sufficient rights to remove players from groups!', login)
				return False
			
			userLevel = self.callFunction(('Acl', 'userGetLevel'), login)
			otherUserLevel = self.callFunction(('Acl', 'userGetLevel'), args[1])

			if userLevel <= otherUserLevel:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'You are not allowed to remove users of higher level than yours from groups!', login)
				return False

			if self.callFunction(('Acl', 'userRemoveGroup'), args[1], args[2]):
				nick = self.callFunction(('Players', 'getPlayerNickName'), args[1])
				self.callMethod(('TmConnector', 'ChatSendServeMessageToLogin'), 'User ' + nick + ' was successfully removed from group ' + args[2], login)
				return True
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'Could not remove player ' + args[1] + ' from group ' + args[2] + '. Did you spell everything correctly?')
				return False

		self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'Unknown command /player ' + str(args), login)
		return False
