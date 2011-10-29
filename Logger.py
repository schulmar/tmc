from PluginInterface import *
import os

class Logger(PluginInterface):
	def __init__(self, pipes, args):
		if isinstance(args, str):
			self.file = open(args, "w")
		else:
			self.file = open("logger.log", "w")
		self.loglevel = 0
		super(Logger, self).__init__(pipes)

	def initialize(self, args):
		#self.callMethod((None,"subscribeEvent"), "TmConnector", "defaultCallback", "log")
		pass

	def log(self, args, level = 0):
		if level >= self.loglevel:
			self.file.write(str(args) + os.linesep)
			self.file.flush()
		else:
			print('Logger: ignored message of level ' + str(level) + ' because current loglevel is '\
					+ str(self.loglevel))
