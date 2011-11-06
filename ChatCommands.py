from PluginInterface import *
from Manialink import *
import os

"""
\file ChatCommands.py
\brief Contains the plugin for general chat commands that are not related to/present in another plugin
"""

class ChatCommands(PluginInterface):
	def __init__(self, pipes, args):
		"""
		\brief Construct the ChatCommands-plugin
		\param pipes The communication pipes to the main process
		\param args additional args for startup
		"""
		super(ChatCommands, self).__init__(pipes)
	
	def initialize(self, args):
		"""
		\brief Initialize the ChatCommands-plugin
		\param args the additional args passed to this plugin
		
		Register all chatcommands that are managed by this plugin
		"""
		registerChatCommand = lambda x,y, z = '': self.callMethod(('TmChat', 'registerChatCommand'), x, ('ChatCommands', y), z)
		rightAdd = lambda x, y: self.callMethod(('Acl', 'rightAdd'), x, y)

		registerChatCommand('echo', 'chat_echo', 'Echo the entered text, to test the systems responsiveness')
		registerChatCommand('listplugins', 'chat_listPlugins', 'List the names of all plugins that are loaded')
	#	registerChatCommand('restart', 'chat_restart')
		registerChatCommand('hello', 'chat_hello', 'Print a hello message to the calling players chat')

		registerChatCommand('player', 'chat_player', 'Manage one player, type /player help for more information')
		rightAdd('ChatCommands.playerAddGroup', 'Add players to groups (that are below the calling players own highest level)')
		rightAdd('ChatCommands.playerRemoveGroup', 'Remove players from groups (that are below the calling players own highest level)')
		registerChatCommand('test', 'chat_test', 'Miscellaneous command for general testing purpose')

	def chat_echo(self, login, args):
		"""
		\brief The echo chat command returns the message inserted
		\param login The login of the calling player
		\param args The text the user inserted
		
		This command is mainly for testing if the plugin-system is responsive.
		"""
		self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), args, login)

	def chat_listPlugins(self, login, args):
		"""
		\brief List the names of all plugins Loaded
		\param login The login of the calling player
		\param args additional arguments
		
		Currently there is no need for additional arguments
		"""
		pluginNames = self.callFunction((None, 'PluginList'))
		self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), str(pluginNames), login)

	def chat_restart(self, login, args):
		"""
		\brief Restart the plugin with the given name
		\param login The login of the calling player
		\param args The name of the plugin to restart
		
		The called function does not work up to now
		"""
		self.callMethod((None, 'restartPlugin'), args)

	def chat_hello(self, login, args):
		"""
		\brief Print a hello message to the chat of the calling player
		\param login The login of the calling player
		\param args Additional arguments(unused)
		"""
		self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'Hi there.', login)

	def chat_player(self, login, args):
		"""
		\brief Manage one player
		\param login The login of the managing player
		\param args The arguments
		"""
		if args == None:
			args = 'help'
		args = args.strip()
		args = args.split()
		commands = {'addgrp' 		: ('... addgrp <player> <group>', 'Add player to a group'),
					'removegrp' 	: ('... removegrp <player> <group>', 'Remove player from a group')}
	#display help for players
		if args[0] == 'help':
			if len(args) == 1:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'Subcommands of /player: ' + ', '.join([i[0] for i in commands]), login)
			else:
				try:
					desc = commands[args[1]]
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								str(desc), login)
				except KeyError:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Unknown /player subcommand "' + args[1] + '"', login)
					return False
			return True
	#add player to group
		elif args[0] == 'addgrp':
			if len(args) != 3:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'/player add needs exactly 2 parameters', login)
				return False

			if not self.callFunction(('Acl', 'userHasRight'), login, 'ChatCommands.playerAddGroup'):
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'You don\'t have sufficient rights to add players to groups', login)
				return False

			userLevel = self.callFunction(('Acl', 'userGetLevel'), login)
			groupLevel = self.callFunction(('Acl', 'groupGetLevel'), args[2])

			if groupLevel > userLevel:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'You can not add players to groups that are higher than yours!', login)
				return False

			if self.callFunction(('Acl', 'userAddGroup'), args[1], args[2]):
				nick = self.callFunction(('Players', 'getPlayerNickName'), args[1])
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'Added player ' + nick + ' to group ' + args[2], login)
				return True
			else:
				self.callFunction(('TmConnector', 'ChatSendServerMessageToLogin'), 
								'Could not add player ' + str(args[1]) + ' to group ' + str(args[2]) + 
								' did you type everything correctly?', login)
				return False
	#remove player from group
		elif args[0] == 'removegrp':
			if len(args) != 3:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'/player remove needs exactly 2 parameters', login)
				return False
			if not self.callFunction(('Acl', 'userHasRight'), args[1], 'ChatCommands.playerRemoveGroup'):
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'You don\'t have sufficient rights to remove players from groups!', login)
				return False
			
			userLevel = self.callFunction(('Acl', 'userGetLevel'), login)
			otherUserLevel = self.callFunction(('Acl', 'userGetLevel'), args[1])

			if userLevel <= otherUserLevel:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'You are not allowed to remove users of higher level than yours from groups!', 
							login)
				return False

			if self.callFunction(('Acl', 'userRemoveGroup'), args[1], args[2]):
				nick = self.callFunction(('Players', 'getPlayerNickName'), args[1])
				self.callMethod(('TmConnector', 'ChatSendServeMessageToLogin'), 'User ' + nick + 
							' was successfully removed from group ' + args[2], login)
				return True
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'Could not remove player ' 
							+ args[1] + ' from group ' + args[2] + '. Did you spell everything correctly?')
				return False

		self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'Unknown command /player ' + 
					str(args), login)
		return False

	def chat_test(self, login, args):
		frame = Frame()
		
		label = Label()
		label['text'] = 'Choose a file for upload'
		frame.addChild(label)
		
		quad = Quad()
		quad['sizen'] = '10 2'
		ml = self.callFunction(('Http', 'getUploadToken'), ('ChatCommands', 'chat_test_upload'), login)
		quad['manialink'] = 'POST(http://' + str(ml[0][0]) + ':' + str(ml[0][1]) \
							+ '?token=' + str(ml[0]) + '&file=inputTrackFile,inputTrackFile)' 
		frame.addChild(quad)
		
		entry = FileEntry()
		entry['posn'] = "0 4"
		entry['sizen'] = "10 2"
		frame.addChild(entry)
		
		self.callMethod(('ManialinkManager', 'displayManialinkToLogin'), frame, 'testUpload', login)
		
	def chat_test_upload(self, entries, data, login):
		trackPath = self.callFunction(('TmConnector', 'GetMapsDirectory'))
		directUploadPath = trackPath + os.path.pathsep + 'direct_upload'
		if not os.path.isdir(directUploadPath):
			os.mkdir(directUploadPath)
		
		directUploadUserPath = directUploadPath + os.path.pathsep + login
		if not os.path.isdir(directUploadUserPath):
			os.mkdir(directUploadUserPath)
			
		fileName = os.path.split(entries['file'])[1]
		filePath = directUploadUserPath + os.path.pathsep + fileName 
			
		f = file(filePath)
		f.write(data)
		f.close()
		
		self.callFunction(('TmConnector', 'InsertMap'), 'direct_upload/' + fileName)