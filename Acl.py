from PluginInterface import *
import MySQLdb

"""
\file Acl.py
\brief Access control list plugin

This plugin provides ACL functionality to any other plugin
"""

class Acl(PluginInterface):
	"""
	\brief The actual plugin-class.
	"""
	def __init__(self, pipes, args):
		"""
		\brief The constructor calls PluginInterface constructor
		\param pipes The communication pipes to the manager
		\param args Other arguments, up to now a dict where the key SuperAdmins contains a list of all superadmin names
		"""
		self.__args = None #Startup arguments
		self.rights = {}
		self.users = {}
		self.groups = {}
		if 'SuperAdmins' in args:
			self.SuperAdmins = args['SuperAdmins']
		else:
			self.SuperAdmins = []
		super(Acl, self).__init__(pipes)

	def initialize(self, args):
		"""
		\brief Create database tables and load users, groups and rights
		\param args contains the same args as in constructor
		"""
		self.__args = args
		self.connection = MySQLdb.connect(user = args['user'], passwd = args['password'], db = args['db'])
		cursor = self.connection.cursor()
		cursor.execute("SHOW TABLES")
		tables = [i[0] for i in cursor.fetchall()]
		if not 'users' in tables:
			cursor.execute(
			"""CREATE TABLE IF NOT EXISTS `users`(
				`id` int NOT NULL auto_increment,
				`name` varchar(50) NOT NULL,
				PRIMARY KEY (`id`),
				UNIQUE KEY `name` (`name`)
			);
			""")
		if not 'groups' in tables:
			cursor.execute(
			"""CREATE TABLE IF NOT EXISTS `groups`(
				`id` int NOT NULL auto_increment,
				`name` text NOT NULL,
				`level` int NOT NULL,
				`description` text NOT NULL,
				`default` BOOLEAN NOT NULL DEFAULT '0',
				PRIMARY KEY (`id`)
			);
			""")
		if not 'rights' in tables:
			cursor.execute(
			"""CREATE TABLE IF NOT EXISTS `rights`(
				`id` int NOT NULL auto_increment,
				`name` text NOT NULL,
				`description` text NOT NULL,
				PRIMARY KEY (`id`)
			);
			""")
		if not 'usersToGroups' in tables:
			cursor.execute(
			"""CREATE TABLE IF NOT EXISTS `usersToGroups`(
				`id` int NOT NULL auto_increment,
				`groupId` int NOT NULL,
				`userId` int NOT NULL,
				PRIMARY KEY (`id`),
				UNIQUE KEY `groupUser` (`groupId`, `userId`)
			);
			""")
		if not 'groupsToRights' in tables:
			cursor.execute(
			"""CREATE TABLE IF NOT EXISTS `groupsToRights`(
				`id` int NOT NULL auto_increment,
				`groupId` int NOT NULL,
				`rightId` int NOT NULL,
				PRIMARY KEY (`id`),
				UNIQUE KEY `groupRight` (`groupId`, `rightId`)
			);
			""")
		if not 'usersToRights' in tables:
			cursor.execute(
			"""CREATE TABLE IF NOT EXISTS `usersToRights`(
				`id` int NOT NULL auto_increment,
				`userId` int NOT NULL,
				`rightId` int NOT NULL,
				PRIMARY KEY (`id`),
				UNIQUE KEY `userRight` (`userId`, `rightId`)
			);
			""")
		cursor.close()
		self.connection.commit()
		self.__loadRights()
		self.__loadUsers()
		self.__loadGroups()

	def shutDown(self):
		"""
		\brief Closes the MySQL connection on shutdown
		"""
		self.connection.close()

	def __loadRights(self):
		"""
		\brief Loads the rights table from database
		"""
		cursor = self.__getCursor()
		cursor.execute('SELECT * FROM `rights`')
		result = cursor.fetchall()
		self.rights = {}
		for i in result:
			self.rights[str(i['name'])] = (int(i['id']), str(i['description']))
		cursor.close()

	def __loadUsers(self):
		"""
		\brief Loads all usernames and their ids from database
		"""
		cursor = self.__getCursor()
		cursor.execute('SELECT `id`,`name` FROM `users`') 
		usersResult = cursor.fetchall()
		self.users = {}
		for i in usersResult:
			#groupsResult = cursor.fetchall()
			self.users[str(i['name'])] = int(i['id'])
		cursor.close()

	def __loadGroups(self):
		"""
		\brief Loads all groups and their ids from database
		"""
		cursor = self.__getCursor()
		cursor.execute('SELECT `id`,`name` FROM `groups`')
		result = cursor.fetchall()
		for i in result:
			self.groups[str(i['name'])] = int(i['id'])
		cursor.close()

	def __getCursor(self):
		"""
		\brief A helper function that returns a dict cursor to the MySQLdb
		\return The dict cursor
		"""
		try:
			self.connection.ping()
		except MySQLdb.OperationalError:
			self.connection = MySQLdb.connect(user = self.__args['user'], 
											passwd = self.__args['password'], 
											db = self.__args['db'])
		return self.connection.cursor(MySQLdb.cursors.DictCursor)

	def getIdFromUserName(self, userName):
		"""
		\brief Transforms a userName to its id
		\param userName the name of the user
		\return the id on success or None if the userName was not found 
		"""
		try:
			return self.users[userName]
		except KeyError:
			self.callMethod(('Logger', 'log'), 'Acl error: user ' + str(userName) + ' unknown in request from ' + str(self.questioner()))
			return None
		
	def getUserNameFromId(self, userId):
		"""
		\brief Search the database for the username
		\param userId The userId of the user to search
		\return The userName if the userId was found or None
		"""
		cursor = self.__getCursor()
		cursor.execute("""
			SELECT `name`
			FROM `users`
			WHERE `userId` = %s
		""", (userId, ))
		userName = cursor.fetchone()
		if userName != None:
			return userName['name']
		else:
			return None

	def getIdFromGroupName(self, groupName):
		"""
		\brief Transforms a groupName to its id
		\param groupName The name of the group 
		\return the groupId on success or None if groupName was not found
		"""
		try:
			return self.groups[groupName]
		except KeyError:
			self.callMethod(('Logger', 'log'), 'Acl error: group ' + groupName + ' unknown in request from ' + str(self.questioner()))
			return None
		
	def getIdFromRightName(self, rightName):
		"""
		\brief Transforms a rightName to its id
		\param rightName The name of the righft
		\return the rightId on success or None if rightName was not found
		"""
		try:
			return self.rights[rightName][0]
		except KeyError:
			self.callMethod(('Logger', 'log'), 'Acl error: right ' + rightName + ' unknown in request from ' + str(self.questioner()))
			return None
		
	def getDefaultGroups(self):
		"""
		\brief Get a list of all default group names
		\return list of groupnames
		"""
		cursor = self.__getCursor()
		cursor.execute("SELECT `name` FROM `groups` WHERE `default`='true'")
		return [r['name'] for r in cursor.fetchall()]

	def userHasRight(self, userName, rightName):
		"""
		\brief Has the user the right?
		\param userName The user in question
		\param rightName The right in question
		\return True if the user has the right, false if the users has not or does not exist or the right does not exist 
		"""
			
		userId = self.getIdFromUserName(userName)
		
		if userId == None:
			return False
		
		for a in self.SuperAdmins:
			try:
				if userId == self.users[a]:
					return True
			except KeyError:
				pass
			
		rightId = self.getIdFromRightName(rightName)
		
		if rightId == None:
			return False
		
		cursor = self.__getCursor()
		cursor.execute('SELECT `id` FROM usersToRights WHERE `userId`=%s and `rightId`=%s', (int(userId), int(rightId)))

		if cursor.fetchone() != None:
			return True
		
		groupList = self.userGetGroups(userName)
		for g in groupList:
			if self.groupHasRight(g, rightName):
				return True

		return False

	def userExists(self, userName):
		"""
		\brief Is the user in the system?
		\param userName The user in question
		\return True or False
		"""
		return (userName in self.users)

	def userAdd(self, userName):
		"""
		\brief add a new user to the system
		\param userName The name of the new user
		"""
		if not self.userExists(userName):
			cursor = self.__getCursor()
			cursor.execute('INSERT INTO `users` (`name`) VALUES (%s)', (userName,))
			cursor.close()
			self.connection.commit()
			self.__loadUsers()
	
	def userAddGroup(self, userName, groupName):
		"""
		\brief add a user to a group
		\param userName The user in question
		\param groupName The group to which the user should be added
		\return True if user is in group, False if user or group do not exist
		"""
		userId = self.getIdFromUserName(userName)
		groupId = self.getIdFromGroupName(groupName)

		if userId == None or groupId == None:
			return False

		cursor = self.__getCursor()
		cursor.execute('SELECT `id` FROM `usersToGroups` WHERE `userId`=%s AND `groupId`=%s', (userId, groupId))
		if cursor.fetchone() == None:
			cursor.execute('INSERT INTO `usersToGroups` (`userId`, `groupId`) VALUES (%s, %s)', (userId, groupId))

		return True

	def userRemoveGroup(self, userName, groupName):
		"""
		\brief Remove user from a group
		\param userName The name of the user in question
		\param groupName The group from which the user should be removed
		\return True if user is not any longer in the group, false if group or user do not exist
		"""
		userId = self.getIdFromUserName(userName)
		groupId = self.getIdFromGroupName(groupName)

		if userId == None or groupId == None:
			return False

		cursor = self.__getCursor()
		cursor.execute('DELETE FROM `usersToGroups` WHERE `userId`=%s AND `groupId`=%s', (userId, groupId))

		return True

	def userAddRight(self, userName, rightName):
		"""
		\brief Grant a right to the user
		\param userName The name of the user in question
		\param rightName The name of the right which to grant
		\return True on success, False if the right or user are unknown
		"""
		userId = self.getIdFromUserName(userName)
		rightId = self.getIdFromRightName(rightName)

		if userId == None or rightId == None:
			return False

		cursor = self.__getCursor()
		cursor.execute('SELECT `id` FROM `usersToRights` WHERE `userId`=%s AND `rightId`=%s',(int(userId), int(rightId)))

		if cursor.fetchone() == None:
			cursor.execute('INSERT INTO `usersToRights` (`userId`, `rightId`) VALUES (%s,%s)', (int(userId), int(rightId)))
			cursor.close()
			self.connection.commit()

		return True

	def userRemoveRight(self, userName, rightName):
		"""
		\brief Revoke right from user
		\param userName The name of the user in question
		\param rightName The right to revoke
		\return True on success, False if the right or user are unknown
		
		Note that this revokes only the right directly from the user.
		If the user is in a group that has this right, hasRight will still return True
		"""
		cursor = self.__getCursor()
		userId = self.getIdFromUserName(userName)
		rightId = self.getIdFromRightName(rightName)

		if userId == None or rightId == None:
			return False

		cursor.execute('DELETE FROM `usersToRights` WHERE `userId`=%s AND `rightId`=%s',(int(userId), int(rightId)))
		cursor.close()
		self.connection.commit()

		return True

	def userGetGroups(self, userName):
		"""
		\brief Get the list of groups the user is in
		\param userName The name of the user in question
		\return The list of groups (empty if user unknown)
		"""
		userId = self.getIdFromUserName(userName)

		if userId == None:
			self.log('Error: Requested groups for non existing user ' + userName)
			return []

		cursor = self.__getCursor()
		cursor.execute("""
			SELECT `groups`.`name` as `name` 
			FROM `usersToGroups` 
			RIGHT JOIN `groups` ON `groupId` = `groups`.`id` 
			WHERE `userId` = %s OR `default` = 1 
			ORDER BY `level` DESC
		""",(int(userId),))
		groupList = cursor.fetchall()

		groupList = [i['name'] for i in groupList]
	
		return groupList

	def userGetLevel(self, userName):
		"""
		\brief Get the highest level of the groups the user is in
		\param userName The user in question
		\return The level or None if no level could be determined
		"""
		groups = self.userGetGroups(userName)
		
		if userName in self.SuperAdmins:
			level = self.groupsGetHighestLevel()
			if level == None:
				return None
			else:
				return level + 1

		if len(groups) > 0:
			return self.groupGetLevel(groups[0])
		
		return None
			
	def userGetDirectRights(self, userName):
		"""
		\brief Get a list of all rights a user has directly 
			(not via group membership)
		\return List of right names or None if the user does not exist
		"""
		userId = self.getIdFromUserName(userName)
		if userId == None:
			return None
		
		#fetch all rights that are directly assigned to the user
		cursor = self.__getCursor()
		cursor.execute("""
			SELECT `name`
			FROM `rights`
			JOIN `usersToRights` ON `rights`.`id` = `usersToRights`.`rightId`
			WHERE `usersToRights`.`userId` = %s
		""", (userId, ))
		return [r['name'] for r in cursor.fetchall()]
			
	def userGetRights(self, userName):
		"""
		\brief Get a list of all rights a user has
		\return List of right names none if user does not exist 
		"""
		rights = self.userGetDirectRights(userName)
		if rights == None:
			return None
		
		#fetch all rights from the groups
		groups = self.userGetGroups(userName)
		for groupName in groups:
			rights.extend(self.groupGetRights(groupName))
		
		#return the list of rights
		return list(set(rights))

	def groupGetAll(self):
		"""
		\brief Get all groups
		\return List of all groups 
			[(groupId, groupName, groupLevel, description, isDefault)]
			
		The list is ordered by descending level 
		"""
		cursor = self.__getCursor()
		cursor.execute("""
			SELECT * FROM `groups`
			ORDER BY `level` DESC
		""")
		return [(g['id'], g['name'], g['level'], g['description'], g['default'])
				for g in cursor.fetchall()]

	def groupExists(self, groupName):
		"""
		\brief Return wether a group with this name exists
		\param groupName The name of the group
		\return True or False
		"""
		return groupName in self.groups

	def groupAdd(self, groupName, description = '', level = 0):
		"""
		\brief Add a new group(Name) to the system
		\param groupName The name of the new group
		\param description A description of the group 
		\param level The level of the new group
		\return True if the group was created, False if it already existed
		"""
		if not self.groupExists(groupName):
			cursor = self.__getCursor()
			cursor.execute('''
				INSERT INTO `groups` (`name`, `level`, `description`) VALUES (%s, %s, %s)
			''', (str(groupName), int(level), str(description)))
			cursor.close()
			self.connection.commit()
			self.__loadGroups()
			return True
		else:
			return False

	def groupRemove(self, groupName):
		"""
		\brief Remove a group from the system
		\param groupName The name of the group to remove
		\return True when the group was deleted
		"""
		groupId = self.getIdFromGroupName(groupName)
		
		if groupId == None:
			return False
		
		cursor = self.__getCursor()
		cursor.execute('DELETE FROM `groups` WHERE `id`=%s', (int(groupId),))
		cursor.execute('DELETE FROM `groupsToRights` WHERE `groupId`=%s', (int(groupId),))
		cursor.execute('DELETE FROM `usersToGroups` WHERE `groupId`=%s', (int(groupId),))
		cursor.close()
		self.connection.commit()
		self.__loadGroups()
		return True
		

	def groupSetDefault(self, groupName, default = True):
		"""
		\brief Set wether a group is default or not
		\param groupName The name of the group to set
		\param default The value to which to set, defaults to True
		"""
		groupId = self.getIdFromGroupName(groupName)
		
		if groupId == None:
			return False
		
		cursor = self.__getCursor()
		cursor.execute("""
			UPDATE `groups` 
			SET `default` = %s
			WHERE `id` = %s
		""", (bool(default), int(groupId)))
		cursor.close()
		self.connection.commit()
		self.__loadGroups()
		
		return True
		

	def groupHasRight(self, groupName, rightName):
		"""
		\brief Has the group the right
		\param groupName The name of the group to check
		\param rightName The name of the right to check
		\return True or False
		"""
		groupId = self.getIdFromGroupName(groupName)
		rightId = self.getIdFromRightName(rightName)

		if groupId == None or rightId == None:
			return False

		cursor = self.__getCursor()
		cursor.execute('SELECT `id` FROM `groupsToRights` WHERE `groupId`=%s AND `rightId`=%s', (int(groupId), int(rightId)))
		if cursor.fetchone() != None:
			return True

		return False

	def groupSetLevel(self, groupName, level):
		"""
		\brief Set the level of a group
		\param groupName The name of the group 
		\param level The new level of the group
		\return True on success, False when the groupName was not found 
		"""
		groupId = self.getIdFromGroupName(groupName)
		
		if groupId == None:
			return False

		cursor = self.__getCursor()
		cursor.execute('UPDATE `groups` SET `level`=%s WHERE `id`=%s', (int(level), groupId))
		cursor.close()
		self.connection.commit()

		return True

	def groupGetLevel(self, groupName):
		"""
		\brief Get the level of the group
		\param groupName The name of the group in question
		\return The level or None if the group was not found
		"""
		groupId = self.getIdFromGroupName(groupName)

		if groupId == None:
			return None

		cursor = self.__getCursor()
		cursor.execute('SELECT `level` FROM `groups` WHERE `id`=%s', (groupId,))

		row = cursor.fetchone()

		if row == None:
			return None
		else:
			return int(row['level'])

	def groupsGetHighestLevel(self):
		"""
		\brief Get the highest level of all groups in the system
		\return The level or None if no groups are defined 
		"""
		cursor = self.__getCursor()
		cursor.execute('SELECT `level` FROM `groups` ORDER BY `level` DESC LIMIT 1')
		g = cursor.fetchone()
		
		if g == None:
			return None

		return g['level']

	def groupAddRight(self, groupName, rightName):
		"""
		\brief Grant a right to the group
		\param groupName The name of the group
		\param rightName The name of the right to grant
		\return True on success, False if the right or group does not exist
		"""
		cursor = self.__getCursor()
		groupId = self.getIdFromGroupName(groupName)
		rightId = self.getIdFromRightName(rightName)

		if groupId == None or rightId == None:
			return False

		cursor.execute('''
			INSERT IGNORE INTO `groupsToRights` (`groupId`, `rightId`) 
			VALUES (%s, %s)
		''', (int(groupId), int(rightId)))
		cursor.close()
		self.connection.commit()
		
		return True
		
	def groupRemoveRight(self, groupName, rightName):
		"""
		\brief Revoke a right from the group
		\param groupName The name of the group
		\param rightName The name of the right to revoke
		\return True on success, False if group or right were not found		
		"""
		cursor = self.__getCursor()
		groupId = self.getIdFromGroupName(groupName)
		rightId = self.getIdFromRightName(rightName)

		if groupId == None or rightId == None:
			return False

		cursor.execute('''
			DELETE FROM `groupsToRights` 
			WHERE `groupId`=%s AND 
			`rightId`=%s
		''', (int(groupId), int(rightId)))
		cursor.close()
		self.connection.commit()
		return True
	
	def groupGetRights(self, groupName):
		"""
		\brief Get all rights of a group
		\param groupName The group whose rights to fetch
		"""
		groupId = self.getIdFromGroupName(groupName)
		if groupId == None:
			return None
		
		cursor = self.__getCursor()
		cursor.execute("""
			SELECT `name` 
			FROM `rights`
			JOIN `groupsToRights` ON `rights`.`id` = `groupsToRights`.`rightId`
			WHERE `groupsToRights`.`groupId` = %s
			ORDER BY `name` ASC
		""", (groupId, ))
		return [r['name'] for r in cursor.fetchall()]
		
	
	def rightGetAll(self):
		"""
		\brief Return the right dictionary
		\return A mapping from all rightnames to their id and description
		"""
		cursor = self.__getCursor()
		cursor.execute('''
			SELECT *
			FROM `rights`
			ORDER BY `name` ASC
		''')
		return [(r['id'], r['name'], r['description'])
				for r in cursor.fetchall()] 

	def rightExists(self, rightName):
		"""
		\brief Is a right of this name defined in the system
		\return True or False
		"""
		return (rightName in self.rights)

	def rightAdd(self, rightName, description):
		"""
		\brief Add a new right to the system
		\param rightName The name of the new right
		\param description A description what this right means
		\return True if the right was added, False if it already exists
		"""
		if not self.rightExists(rightName):
			cursor = self.__getCursor()
			cursor.execute('SELECT `id` FROM `rights` WHERE `name`=%s', (str(rightName),))
			if cursor.fetchone() != None:
				return False
			cursor.execute('INSERT INTO `rights` (`name`, `description`) VALUES (%s, %s)', (str(rightName), str(description)))
			cursor.close()
			self.connection.commit()
			self.__loadRights()
			return True

		return False
		
		
	def removeRight(self, rightName):
		"""
		\brief Remove a right from the system
		\param rightName The name of the right to remove
		\return True on success
		"""
		rightId = self.getIdFromRightName(rightName)
		cursor = self.__getCursor()
		cursor.execute('DELETE FROM `rights` WHERE `id`=%s', (int(rightId),))
		cursor.execute('DELETE FROM `groupsToRights` WHERE `rightId`=%s', (int(rightId),))
		cursor.execute('DELETE FROM `usersToRights` WHERE `rightId`=%s', (int(rightId),))
		cursor.close()
		self.connection.commit()
		return True
