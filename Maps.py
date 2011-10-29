from PluginInterface import *
import MySQLdb

class Maps(PluginInterface):
	def __init__(self, pipes, args):
		super(Maps, self).__init__(pipes)

	def initialize(self, args):
		self.connection = MySQLdb.connect(user = args['user'], passwd = args['password'], db = args['db'])

