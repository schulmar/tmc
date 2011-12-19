from PluginInterface import *
import os
import re

"""
\file TmChat.pd
\brief Contains the chat manager plugin
"""

class TmChat(PluginInterface):
	"""
	\brief The chat manager plugin
	
	This plugin handles chat commands
	"""
	def __init__(self, pipes, args):
		"""
		\brief Construct the plugin
		\param pipes The communication pipes to the pluginManager
		\param args Additional startup arguments
		"""
		self.commands = {}
		super(TmChat, self).__init__(pipes)

	def initialize(self, args):
		"""
		\brief Initialize the plugin
		\param args Startup arguments (should be emtpy)
		"""
		self.callMethod((None , 'subscribeEvent'), 'TmConnector', 'PlayerChat', 'PlayerChat')
		self.registerChatCommand('help', ('TmChat', 'chat_help'), 'List all available chat commands.')

	def PlayerChat(self, Uid, login, text, isRegisteredCmd):
		"""
		\brief Callback on player chat
		\param Uid The player Uid
		\param login The login of the player
		\param text The text the player wrote
		\param isRegisteredCmd Is this a registered command (leading /)
		"""
		if len(text) > 0:
			text = text.strip()
			if text[0] == '/':
				self.processCommand(login, text[1:])

	def processCommand(self, login, text):
		"""
		\brief Finds the callback for the command
		\param login The login of the calling player
		\param text The text of the command
		"""
		parts = text.split(' ', 1)
		if parts[0] in self.commands:
			cb = self.commands[parts[0]][0]
			if len(parts) > 1:
				arg = parts[1]
			else:
				arg = None
			self.callMethod(cb, login, arg)
			return True
		else:
			self.log('Error: Chat command ' + parts[0] + ' not known')
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'Error: Chat command ' + parts[0] + ' unnknown', login)
			return False

	def registerChatCommand(self, name, callback, description = 'No description'):
		"""
		\brief Register a command callback
		\param name The name of the chatcommand
		\param callback The callback 
		\param description A short description of the chat command
		"""
		if name in self.commands:
			callback = self.commands[name]
			self.callMethod(('Logger', 'log'), 'Plugin Chat: Could not register chat-command"' + name \
			+ '" as it already is attached to ' + callback[0] + '.' + callback[1] + '"', 1)
		else:
			self.commands[name] = (callback, description)
			self.callMethod(('Logger', 'log'), 'Plugin Chat: Registered chat-command "' \
								+ name + '"', 0)
	
	def unregisterChatCommand(self, name):
		"""
		\brief Unregister a registered chat command
		\param name THe name of the command to unregister
		"""
		if name in self.commands:
			del self.commands[name]

	def chat_help(self, login, args):
		"""
		\brief Display a help text in the chat
		\param login The player who needs help
		\param args Additional args for help
		"""
		try:
			args = args.strip()
		except AttributeError:
			pass

		if not args in self.commands:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'Currently supported chat-commands: ' + ', '.join(self.commands.keys()), login)
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'Chat-command "' + str(args) + '": ' + self.commands[args][1], login)
			
			
		
