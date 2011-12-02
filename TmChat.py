from PluginInterface import *
import os
import re

class TmChat(PluginInterface):
	def __init__(self, pipes, args):
		self.commands = {}
		super(TmChat, self).__init__(pipes)

	def initialize(self, args):
		self.callMethod((None , 'subscribeEvent'), 'TmConnector', 'PlayerChat', 'PlayerChat')
		self.registerChatCommand('help', ('TmChat', 'chat_help'), 'List all available chat commands.')

	def PlayerChat(self, *args):
		if len(args[2]) > 0:
			text = args[2].strip()
			if text[0] == '/':
				self.processCommand(args[1], text[1:])

	def processCommand(self, login, text):
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
		if name in self.commands:
			callback = self.commands[name]
			self.callMethod(('Logger', 'log'), 'Plugin Chat: Could not register chat-command"' + name \
			+ '" as it already is attached to ' + callback[0] + '.' + callback[1] + '"', 1)
		else:
			self.commands[name] = (callback, description)
			self.callMethod(('Logger', 'log'), 'Plugin Chat: Registered chat-command "' \
								+ name + '"', 0)
	
	def unregisterChatCommand(self, name):
		if name in self.commands:
			del self.commands[name]

	def chat_help(self, login, args):
		try:
			args = args.strip()
		except AttributeError:
			pass

		if not args in self.commands:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'Currently supported chat-commands: ' + ', '.join(self.commands.keys()), login)
		else:
			self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 'Chat-command "' + str(args) + '": ' + self.commands[args][1], login)
			
			
		
