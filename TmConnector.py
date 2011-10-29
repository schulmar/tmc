from PluginInterface import *
import Gbx
import threading
import xmlrpclib
import os
import functools
import xml.parsers.expat

class TmConnector(PluginInterface):
	def __init__(self, pipes, args):
		self.listener = Gbx.Client(args[0])
		self.questioner = Gbx.Client(args[0])
		self.args = args
		super(TmConnector, self).__init__(pipes)

	def initialize(self, args):
		self.startListener()
		self.startQuestioner()
		self.t_id = threading.Thread(target = self.__Poll)
		self.t_id.start()

	def startListener(self):
		self.listener.init()
		self.listener.Authenticate(self.args[1], self.args[2])
		self.listener.EnableCallbacks(True)
		self.listener.set_default_method(self.__default_callback)
		self.listener.SetApiVersion("2011-10-06")

	def startQuestioner(self):
		self.questioner.init()
		self.questioner.Authenticate(self.args[1], self.args[2])
		self.listener.SetApiVersion("2011-10-06")

	def __Poll(self):
		while True:
			try:
				self.listener.tick()
			except (Gbx.ProtocolError, xml.parsers.expat.ExpatError, Gbx.ConnectionError) as e:
				self.callMethod(('Logger','log'), 'Error: ' + str(e))
			except xmlrpclib.Fault as f:
				self.callMethod(('Logger','log'), 'Error: ' + str(f))

	def __default_callback(self, *args):
		name = args[0].split('.')[1]
		self.signalEvent(name, *args[1:])
		self.signalEvent("defaultCallback", name, *args[1:])

	def __getattr__(self, name):
		attr = functools.partial(self.__wrapper, getattr(self.questioner, name))
		return attr

	def __wrapper(self, function, *args):
		try:
			result = function(*args)
			return result
		except (xml.parsers.expat.ExpatError, Gbx.ProtocolError, Gbx.ConnectionError) as e:
			self.callMethod(('Logger','log'), 'Error('+str(e)+'): Called method ' + str(function) + \
								' with args ' + str(args) + os.linesep +\
								'Restarting Gbx.Client')
			return None
		except xmlrpclib.Fault as f:
			self.callMethod(('Logger','log'), 'Error: ' + str(args) + str(f))
			return None
