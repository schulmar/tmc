from PluginInterface import *
import MySQLdb

"""
\file Maps.py
\brief Contains the Maps plugin

This plugin should manage the maps on the server
"""

class Maps(PluginInterface):
	"""
	\brief The Maps plugin class derived from PluginInterface
	"""
	def __init__(self, pipes, args):
		"""
		\brief Construct the class
		\param pipes The pipes to the PluginManager process
		\param args Additional userdefined args 
		"""
		self.__currentMaps = []
		super(Maps, self).__init__(pipes)

	def initialize(self, args):
		"""
		\brief Initialize the plugin on startup
		\params args The user parameters for the plugin
		
		Setup the database connection create tables if necessary...
		"""
		self.connection = MySQLdb.connect(user = args['user'], passwd = args['password'], db = args['db'])
		cursor = self.__getCursor()
		cursor.execute("""
		CREATE TABLE IF NOT EXISTS `maps` (
		`Id` mediumint(9) NOT NULL auto_increment, 
		`Uid` varchar(27) NOT NULL default '', 
		`Name` varchar(100) NOT NULL default '',
		`Author` varchar(30) NOT NULL default '',
		`Environment` varchar(10) NOT NULL default '',
		PRIMARY KEY (`Id`),
		UNIQUE KEY `Uid` (`Uid`)
		);
		""");
		cursor.close()
		self.connection.commit()
		self.__getMapListFromServer()
		
	def __getCursor(self):
		"""
		\brief A helper function that returns a dict cursor to the MySQLdb
		\return The dict cursor
		"""
		return self.connection.cursor(MySQLdb.cursors.DictCursor)
	
	def __getMapListFromServer(self):
		"""
		\brief Retrieve the servers list of maps
		"""
		self.__currentMaps = self.callFunction(('TmConnector', 'GetMapList'), 10000, 0)
		print(self.__currentMaps)
		