from PluginInterface import *
import os
import time

"""
\file Logger.py
\brief Contains the logger plugin

This plugin provides an interface for logging.
It can be replaced by any other plugin that provides the same interface,
but it should take the same arguments.
"""

class Logger(PluginInterface):
	"""
	\brief The logger class plugin
	"""
	def __init__(self, pipes, args):
		"""
		\brief The constructor
		\param pipes The pipes for communication with the PluginManager, passed to the super constructor
		\param args The arguments to this logger, up to now only the name of the log-file
		"""
		if isinstance(args, str):
			self.file = open(args, "w")
		else:
			self.file = open("logger.log", "w")
		self.loglevel = 0
		super(Logger, self).__init__(pipes)

	def initialize(self, args):
		"""
		\brief Initializing the logger on startup
		
		Nothing to do up to now
		"""
		#self.callMethod((None,"subscribeEvent"), "TmConnector", "defaultCallback", "log")
		pass

	def log(self, args, level = 0):
		"""
		\brief Log one line with the given level
		\param args The args to log
		
		Depending on the loglevel messages can be ignored.
		"""
		if level >= self.loglevel:
			timeStamp = time.strftime('%b %d %H:%M:%S')
			self.file.write(timeStamp + ' ' + str(args) + os.linesep)
			self.file.flush()
		else:
			print('Logger: ignored message of level ' + str(level) + ' because current loglevel is '\
					+ str(self.loglevel))
