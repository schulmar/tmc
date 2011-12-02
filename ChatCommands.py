from PluginInterface import *
from Manialink import *
import os
from WindowElements import *

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

		rightAdd('ChatCommands.playerAddGroup', 
				'Add players to groups (that are below the calling players own highest level)')
		rightAdd('ChatCommands.playerRemoveGroup', 
				'Remove players from groups (that are below the calling players own highest level)')
		rightAdd('ChatCommands.playerDisplayRights',
				'Display the rights another player has.')
		rightAdd('ChatCommands.playerChangeRight',
				'Change a right of a user.')
		registerChatCommand('player', 'chat_player', 'Manage one player, type /player help for more information')
		
		rightAdd('ChatCommands.groupDisplay',
				'Display all groups that are defined.')
		registerChatCommand('group', 'chat_group', 'Manage user groups. type /group help for more information')
		
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
					'removegrp' 	: ('... removegrp <player> <group>', 'Remove player from a group'),
					'rights'		: ('... rights <player>', 'Manage the rights of a player')}
	#display help for players
		if args[0] == 'help':
			if len(args) == 1:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'Subcommands of /player: ' + ', '.join(commands.keys()), login)
			else:
				try:
					desc = commands[args[1]]
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'command /player ' + args[1] + ': ' + str(desc), login)
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
			if not self.callFunction(('Acl', 'userHasRight'), login, 'ChatCommands.playerRemoveGroup'):
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
		elif args[0] == 'rights':
			if len(args) != 2:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'/player remove needs exactly one parameter', login)
				return False
			if (login != args[1] and not
				self.callFunction(('Acl', 'userHasRight'), login, 
								'ChatCommands.playerDisplayRights')):
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'You don\'t have sufficient rights to display the rights of players!', login)
				return False
			userRights = self.callFunction(('Acl', 'userGetDirectRights'), args[1])
			if userRights == None:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'Unknown user ' + args[1], login)
				return False
			allRights = self.callFunction(('Acl', 'rightGetAll'))
			positive = [(r[0], r[1][1], True) for r in allRights.items() if r[0] in userRights]
			negative = [(r[0], r[1][1], False) for r in allRights.items() if r[0] not in userRights]
		
			nickName = self.callFunction(('Players', 'getPlayerNickname'), args[1])
			
			window = RightsWindow( nickName + '$z\'s rights')
			window.setSize((85, 70))
			window.setPos((-40, 35))
			window.setSetRightCallback(('ChatCommands', 'cb_setRight'), (args[1], ))
			if self.callFunction(('Acl', 'userHasRight'), login, 
								'ChatCommands.userChangeRight'):
				window.setEditable(True)
			window.setRights(positive + negative)
			self.callMethod(('WindowManager', 'displayWindow'), login, 
						'ChatCommands.userRights', window, True)
		elif args[0] == 'rightadd':
			self.callMethod(('Acl', 'userAddRight'), args[1], args[2])
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'Granted right ' + args[1] + ' to player ' + args[1], login)
		elif args[1] == 'rightremove':
			self.callMethod(('Acl', 'userRemoveRight'), args[1], args[2])
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'Revoked right ' + args[1] + ' from player ' + args[1], login)
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'Unknown command /player ' + 
					str(args), login)
		return False
	
	def cb_setRight(self, entries, login, rightName, value, player):
		"""
		\brief Callback for setting rights of users
		\param entries Should be emtpy
		\param login The login of the calling player
		\param rightName The name of the right to set
		\param value The value to set the right to
		\param the player to manage
		"""
		if value:
			self.chat_player(login, 'rightadd ' + player + ' ' +  rightName)
		else:
			self.chat_player(login, 'rightremove ' +  player + ' ' +  rightName)
		self.chat_player(login, 'rights ' + player)
		
	def chat_group(self, login, args):
		"""
		\brief Recieves chatcommands concerning groups
		\param login The login of the invoking player
		\param args the additional args passed by the player
		"""
		if args == None:
			args = 'display'
			
		args = args.split()
		
		subcommands = {	'help' 		: 'display all subcommands and their description',
						'display' 	: 'display all known groups',
						'add' 		: 'Add a new group (/group add <newGroupName>)',
						'remove' 	: 'Remove an existing group (/group remove <existingGroupName>)' 
					}
		
		if args[0] == 'help':
			if len(args) == 2:
				try:
					description = subcommands[args[1]]
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Help for subcommand /group ' + args[1]
								+ ': ' + description, login)
				except KeyError:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Unknown subcommand /group ' + args[1], login)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Available subcommands for /group: ' + 
								str(subcommands.keys()), 
								login)
		elif args[0] == 'display':
			groups = self.callFunction(('Acl', 'groupGetAll'))
			if self.callFunction(('Acl', 'userHasRight'), login, 
								'ChatCommands.groupDisplay'):
				if len(groups) > 0:
					window = TableStringsWindow('All user groups')
					window.setSize((80, 70))
					window.setPos((-40, 35))
					window.setTableStrings(groups, 15, 
						(5, 15, 50, 5, 5), 
						('Id', 'Name', 'Description', 'Level', 'default'))
				else:
					self.callMethod(('TmConnector', 
									'ChatSendServerMessageToLogin'),
									'There are no groups to view', login)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'You have insufficient rights to view the groups.', 
						login)
		elif args[0] == 'add':
			if self.callFunction(('Acl', 'userHasRight'), login, 'ChatCommands.addGroup'):
				if len(args) != 2:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'Command /group add takes exactly one parameter (<newGroupName>)', 
						login)
					return False
				
				self.callMethod(('Acl', 'groupAdd'), args[1])
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'Added new group ' + args[1] + ' to group list. You may'
						+ ' now define the groups rights and add users to it.', 
						login)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'You have insufficient rights to add new groups.', 
						login)	
		elif args[0] == 'remove':
			if self.callFunction(('Acl', 'userHasRight'), login, 'ChatCommands.removeGroup'):
				if len(args) != 2:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'Command /group remove takes exactly one parameter (<existingGroupName>)', 
						login)
					return False
				
				if self.callFunction(('Acl', 'groupExists'), args[1]):
					window = YesNoDialog('Do you really want to delete the group ' 
										+ args[1] + '?')
					window.setSize((30, 10))
					window.setPos((-15, 10))
					window.setAnswerCallback(('ChatCommands', 'cb_removeGroup'),
											 args[1])
					self.callMethod(('WindowManager', 'displayWindow'), login,
								'ChatCommands.deleteGroupDialog', window) 
				else:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Error: No such group ' + args[1], login)			
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'You have insufficient rights to remove groups.', 
						login)	

	def cb_removeGroup(self, entries, login, answer, groupName):
		"""
		\brief The callback that gets called when deleting a group
			was approved/rejected
		\param entries Should be empty
		\param login The login of the calling player
		\param answer The answer the player gave to the dialog
		\param groupName The name of the group to delete
		"""
		if answer:
			if self.callFunction(('Acl', 'userHasRight'), login, 'ChatCommands.removeGroup'):
				self.callMethod(('Acl', 'groupRemove'), groupName)
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Group ' + groupName + ' successfully deleted', 
								login)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'You have insufficient rights to remove groups.', 
						login)	
	def chat_test(self, login, args):
		"""
		\brief A test function for arbitrary funictionality
		\param login The login of the calling player
		\param args Additional command line params
		
		Currently displays a comment form		
		"""
		"""
		ci = CommentInput(('ChatCommands', 'comment_enter'), 'An awfully long title that never should occur in real applications')
		ci.setSize((80, 60))
		ci.setPos((-40, 30))
		self.callMethod(('WindowManager', 'displayWindow'), login, 'ChatCommands.commentTest', ci)
		"""
		pass