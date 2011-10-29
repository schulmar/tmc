from PluginInterface import *

class Music(PluginInterface):
	def __init__(self, pipes, args):
		super(Music, self).__init__(pipes)

	def initialize(self, args):
		self.songs = args
		self.current = 0
		self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'BeginRound', 'nextSong')
		self.callMethod(('TmChat', 'registerChatCommand'), 'music', ('Music', 'chat_music'))

	def chat_music(self, *args):
		pass	

	def nextSong(self, *args):
		pass
