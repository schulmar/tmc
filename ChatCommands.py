from PluginInterface import *
from Manialink import *
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
		self.__adminEmail = None #The admin email address
		try:
			self.__adminEmail = args['admin-email']
		except KeyError:
			pass
	
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
		rightAdd('ChatCommands.playerDisplayGroups', 
				'Display all groups that a user is member of.')
		rightAdd('ChatCommands.playerDisplayRights',
				'Display the rights another player has.')
		rightAdd('ChatCommands.playerChangeRight',
				'Change a right of a user.')
		registerChatCommand('player', 'chat_player', 'Manage one player, type /player help for more information')
		
		rightAdd('ChatCommands.groupDisplay',
				'Display all groups that are defined.')
		rightAdd('ChatCommands.addGroup',
				'Add a new group to the group list.')
		rightAdd('ChatCommands.removeGroup',
				'Remove an existing group from the right list.')
		rightAdd('ChatCommands.groupDisplayRights',
				'Display the rights of a group.')
		rightAdd('ChatCommands.groupChangeRight',
				'Change the rights of a group.')
		rightAdd('ChatCommands.userAddRight',
				'Grant a right to an user.')
		rightAdd('ChatCommands.userRemoveRight',
				'Revoke a right from an user.')
		rightAdd('ChatCommands.groupAddRight',
				'Grant a right to a group.')
		rightAdd('ChatCommands.groupRemoveRight',
				'Revoke a right from a group.')
		rightAdd('ChatCommands.changeGroupDefault',
				'Set the default state of a group')
		registerChatCommand('group', 'chat_group', 'Manage user groups. type /group help for more information')
		
		registerChatCommand('test', 'chat_test', 'Miscellaneous command for general testing purpose')
		
		registerChatCommand('records', 'chat_records', 'Display the list of local records')
		
		registerChatCommand('contact', 'chat_contact', 'Display the contact address of the server admin.')
		
		registerChatCommand('gg', 'chat_gg', 'Congratulate other players')

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
					'groups'		: ('... groups <player>', 
									'Display all groups of the player.'),
					'rights'		: ('... rights <player>', 'Manage the rights of a player'),
					'addright'		: ('... addright <player> <right>', 
											'Grant a right to a player'),
					'removeright'	: ('... removeright <player> <right>', 
											'Revoke a right from a player')}
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
				nick = self.callFunction(('Players', 'getPlayerNickname'), args[1])
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
				nick = self.callFunction(('Players', 'getPlayerNickname'), args[1])
				self.callMethod(('TmConnector', 'ChatSendServeMessageToLogin'), 'User ' + nick + 
							' was successfully removed from group ' + args[2], login)
				return True
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'Could not remove player ' 
							+ args[1] + ' from group ' + args[2] + '. Did you spell everything correctly?')
				return False
		elif args[0] == 'groups':
			if self.callFunction(('Acl', 'userHasRight'), login, 
								'ChatCommands.playerDisplayGroups'):
				if len(args) != 2:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'Command /player groups takes exactly 1 parameter (<login>)', 
							login)
					return
				groups = self.callFunction(('Acl', 'userGetGroups'), args[1])
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							str(groups), login)
		elif args[0] == 'rights':
			if len(args) != 2:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'/player rights needs exactly one parameter (<playerLogin>)', login)
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
			rights = [(r[1], r[2], (r[1] in userRights)) 
						for r in allRights]
		
			nickName = self.callFunction(('Players', 'getPlayerNickname'), args[1])
			
			window = RightsWindow('Player ' + nickName + '$z\'s rights')
			window.setSize((85, 70))
			window.setPos((-40, 35))
			window.setSetRightCallback(('ChatCommands', 'cb_setRight'), (args[1], ))
			if self.callFunction(('Acl', 'userHasRight'), login, 
								'ChatCommands.userChangeRight'):
				window.setEditable(True)
			window.setRights(rights)
			self.callMethod(('WindowManager', 'displayWindow'), login, 
						'ChatCommands.userRights', window, True)
		elif args[0] == 'addright' or args[0] == 'grant':
			if len(args) != 3:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'/player addright needs exacty 2 parameters ' + 
							'(<playerLogin>, <rightName>)')
				return False
			if self.callFunction(('Acl', 'userHasRight'), login, 
								'ChatCommands.userAddRight'):
				self.callMethod(('Acl', 'userAddRight'), args[1], args[2])
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'Granted right ' + args[2] + ' to player ' + args[1], login)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'You have insufficient rights to grant rights to users.', login)
		elif args[0] == 'removeright' or args[0] == 'revoke':
			if len(args) != 3:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'/player removeright needs exacty 2 parameters ' + 
							'(<playerLogin>, <rightName>)')
				return False
			if self.callFunction(('Acl', 'userHasRight'), login,
								'ChatCommands.userRemoveRight'):
				self.callMethod(('Acl', 'userRemoveRight'), args[1], args[2])
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'Revoked right ' + args[2] + ' from player ' + args[1], login)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'You have insufficient rights to revoke rights from users', login)
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
			self.chat_player(login, 'grant ' + player + ' ' +  rightName)
		else:
			self.chat_player(login, 'revoke ' +  player + ' ' +  rightName)
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
						'add' 		: 'Add a new group (/group add <newGroupName> <description>)',
						'remove' 	: 'Remove an existing group (/group remove <existingGroupName>)' ,
						'removeright' : 
							'Revoke a right from a group (/group removeright <groupName> <rightName>)',
						'addright' 	: 
							'Grant a right to a group (/group addright <groupName> <rightName>)',
						'default'	:
							'Manage if any user is in this group by default ' +
							'(/group default <groupName> <isDefault>)'
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
					window = TableWindow('All user groups')
					window.setSize((80, 60))
					window.setPos((-40, 35))
					window.setIcon('Icons128x128_1', 'Buddies')
					lines = []
					for g in groups:
						line = []
					#idLabel
						idLabel = Label()
						idLabel['text'] = g[0]
						idLabel['sizen'] = '3 2'
						idLabel['posn'] = '1 0'
						idLabel.setCallback(('ChatCommands', 'cb_chatRemoveGroup'),
										g[1])
						line.append(idLabel)
						
					#nameLabel
						nameLabel = Label()
						nameLabel['text'] = g[1]
						nameLabel['sizen'] = '14 2'
						nameLabel.setCallback(('ChatCommands', 'cb_chatGroupRights'), g[1])
						line.append(nameLabel)
						
					#levelLabel
						levelLabel = Label()
						levelLabel['text'] = g[2]
						levelLabel['sizen'] = '4 2'
						line.append(levelLabel)
						
					#descriptionLabel
						descriptionLabel = Label()
						descriptionLabel['text'] = g[3]
						descriptionLabel['sizen'] = '44 2'
						line.append(descriptionLabel)
						
					#defaultLabel
						defaultLabel = Label()
						defaultLabel['sizen'] = '5 2'
						if g[4]:
							defaultLabel['text'] = 'yes'
							defaultLabel.setCallback(('ChatCommands', 'cb_setGroupDefault'),
													g[1],'no')
						else:
							defaultLabel['text'] = 'no'
							defaultLabel.setCallback(('ChatCommands', 'cb_setGroupDefault'), 
													g[1], 'yes')
						line.append(defaultLabel)
						lines.append(line)
					window.setTable(lines, 15, (3, 15, 5, 45, 10), 
						('Id', 'Name', 'Level', 'Description', 'default'))
					self.callMethod(('WindowManager', 'displayWindow'),	login, 
								'ChatCommands.groupsList', window, True)
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
				if len(args) < 3:
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'Command /group add takes exactly two parameters' + 
						' (<newGroupName> <description>)', 
						login)
					return False
				
				self.callMethod(('Acl', 'groupAdd'), args[1], ' '.join(args[2:]))
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'Added new group ' + args[1] + ' to group list. You may'
						+ ' now define the groups rights and add users to it.', 
						login)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'You have insufficient rights to add new groups.', 
						login)	
		elif args[0] == 'remove' or args[0] == 'delete':
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
		elif args[0] == 'rights':
			if len(args) != 2:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'/group rights needs exactly one parameter (<groupName>)', login)
				return False
			if (login != args[1] and not
				self.callFunction(('Acl', 'userHasRight'), login, 
								'ChatCommands.groupDisplayRights')):
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'You don\'t have sufficient rights to display the rights of groups!', login)
				return False
			groupRights = self.callFunction(('Acl', 'groupGetRights'), args[1])
			if groupRights == None:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'Unknown group ' + args[1], login)
				return False
			allRights = self.callFunction(('Acl', 'rightGetAll'))
			rights = [(r[1], r[2], (r[1] in groupRights)) 
						for r in allRights]
			
			window = RightsWindow('Group ' +  args[1] + '$z\'s rights')
			window.setSize((85, 70))
			window.setPos((-40, 35))
			window.setSetRightCallback(('ChatCommands', 'cb_setGroupRight'), (args[1], ))
			if self.callFunction(('Acl', 'userHasRight'), login, 
								'ChatCommands.groupChangeRight'):
				window.setEditable(True)
			window.setRights(rights)
			self.callMethod(('WindowManager', 'displayWindow'), login, 
						'ChatCommands.groupRights', window, True)
		elif args[0] == 'default':
			if not self.callFunction(('Acl', 'userHasRight'), login, 
									'ChatCommands.changeGroupDefault'):
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'You have insufficient rights to set' + 
							' the default state of groups.' , login)
				return False
			if len(args) != 3:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'/group default needs exactly two parameters' + 
							' (<groupName>, <isDefault>)', login)
				return False
			if self.callFunction(('Acl', 'groupExists'), args[1]):
				if args[2] == 'yes':
					self.callMethod(('Acl', 'groupSetDefault'), args[1], True)
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Group ' + args[1] +
								' is now a default group.', login)
				elif args[2] == 'no':
					self.callMethod(('Acl', 'groupSetDefault'), args[1], False)
					self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Group ' + args[1] +
								' is not default group (anymore).', login)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
								'Group ' + args[1] + ' does not exist.', login)
				
		elif args[0] == 'addright' or args[0] == 'grant':	
			if len(args) != 3:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'/group addright needs exacty 2 parameters ' + 
							'(<groupName>, <rightName>)')
				return False
			if self.callFunction(('Acl', 'userHasRight'), login, 
								'ChatCommands.groupAddRight'):
				self.callMethod(('Acl', 'groupAddRight'), args[1], args[2])
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'Granted right ' + args[2] + ' to group ' + args[1], login)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'You have insufficient rights to grant rights to groups.', login)
		elif args[0] == 'removeright' or args[0] == 'revoke':
			if len(args) != 3:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'/group removeright needs exacty 2 parameters ' + 
							'(<groupNamp>, <rightName>)')
				return False
			if self.callFunction(('Acl', 'userHasRight'), login,
								'ChatCommands.groupRemoveRight'):
				self.callMethod(('Acl', 'groupRemoveRight'), args[1], args[2])
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
							'Revoked right ' + args[2] + ' from group ' + args[1], login)
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'You have insufficient rights to revoke rights from groups.', login)
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
					'Unknown subcommand /group ' + args[0], 
					login)	

	def cb_chatGroupRights(self, entries, login, groupName):
		"""
		\brief Convenience callback for the group rights
		\param entries Should be emtpy
		\param login THe login of the calling player
		\param groupName The group whose rights to manage
		"""
		self.callMethod(('WindowManager', 'closeWindow'), {},
					login, 'ChatCommands.groupsList')
		self.chat_group(login, 'rights ' + groupName)

	def cb_chatRemoveGroup(self, entries, login, groupName):
		"""
		\brief Callback for remove from group list display
		"""
		self.chat_group(login, 'remove ' + groupName)
		self.chat_group(login, 'display')

	def cb_setGroupDefault(self, entries, login, groupName, isDefault):
		"""
		\brief Set a group as (non)default group
		\param entries Should be emtpy
		\param login The login of the invoking player
		\param groupName The group to (un)set default
		\param isDefault The value to set default to
		"""
		self.chat_group(login, 'default ' + groupName + ' ' + isDefault)
		self.chat_group(login, 'display')

	def cb_removeGroup(self, entries, login, answer, groupName):
		"""
		\brief The callback that gets called when deleting a group
			was approved/rejected
		\param entries Should be empty
		\param login The login of the calling player
		\param answer The answer the player gave to the dialog
		\param groupName The name of the group to delete
		"""
		#hide the dialog window
		self.callMethod(('WindowManager', 'closeWindow'), {}, login, 
					'ChatCommands.deleteGroupDialog')
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
	def cb_setGroupRight(self, entries, login, rightName, value, groupName):
		"""
		\brief Change the right of a group
		\param entries Should be emtpy
		\param login The login of the managing player
		\param rightName The right to change
		\param value Should the right be granted or revoked
		\param groupName The group to manage
		"""
		if value:
			self.chat_group(login, 'grant ' + groupName + ' ' +  rightName)
		else:
			self.chat_group(login, 'revoke ' +  groupName + ' ' +  rightName)
		self.chat_group(login, 'rights ' + groupName)
		
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
	
	def recordsReactor(self, login):
		"""
		\brief Create the records reactor quad
		"""
		quad = Quad()
		quad['actionkey'] = '2'
		quad['posn'] = '-100 - 100'
		quad['sizen'] = '0 0'
		quad.setCallback(('ChatCommands', 'cb_recordsReactor'))
		self.callMethod(('ManialinkManager', 'displayManialinkToLogin'),
					quad, 'ChatCommands.recordShortcut', login)
		
	def cb_recordsReactor(self, entries, login):
		"""
		\brief Display the records window to the player
		"""
		self.chat_records(login, None)
	
	def chat_records(self, login, args):
		"""
		\brief Chat function for displaying records
		\param login The asking player
		\param args Additional arguments
		"""
		records = self.callFunction(('Records', 'getLocals'))
		mapInstance = self.callFunction(('Maps', 'getCurrentMap'))
		if len(records) == 0:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'Currently there are no local records on this map.', login)
		else:
			strings = [(
						r['rank'],
						'{:d}:{:2.3f}'.format(r['time'] // 60000, (r['time'] % 60000) / 1000.0),
						self.callFunction(('Players', 'getPlayerNickname'), r['name'])
					) for r in records]
			window = TableStringsWindow('Local records on ' + mapInstance['Name'])
			window.setSize((50, 70))
			window.setPos((-25, 40))
			window.setTableStrings(strings, 15, (5, 10, 30), ('Rank', 'Time', 'Name'))
			self.callMethod(('WindowManager', 'displayWindow'), login, 'ChatCommands.Records',
						window)
			
	def chat_contact(self, login, args):
		"""
		\brief Print out the contact address of the admin
		\param login The login of the calling player
		\param args Additional arguments
		"""
		if self.__adminEmail != None:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
						'Contact the admin under $l' + 
						str(self.__adminEmail) + '$l', login)
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
						'It seems the admin forgot the contact email address.',
						login)
			
	def chat_gg(self, login, args):
		"""
		\brief Congratulate other players
		"""
		nick = self.callFunction(('Players', 'getPlayerNickname'), login)
		if args == None:
			self.callMethod(('TmConnector', 'ChatSendServerMessage'),
						'[' + nick +  '$z$g] $iGood game all!')
		else:
			nick2 = self.callFunction(('Players', 'getPlayerNickname'), args.strip())
			if nick2 != '':
				self.callMethod(('TmConnector', 'ChatSendServerMessage'),
						'[' + nick +  '$z$g] $iGood game ' + nick2 + '$z$g!')
			else:
				self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
							'Unknown user "' + args + "'", login)	