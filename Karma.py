"""
\file Karma.py
\brief This file contains a plugin that provides a karma system for anything
"""

from PluginInterface import *
import MySQLdb

class Karma(PluginInterface):
    """
    \brief An universal karma class
    
    This class provides karma to any class of objects that is indexed 
    via integers. Users can vote, comment and flag as well as answering
    on comments.
    """
    
    __connection = None#the database connection object
    __types = {}#A mapping from type names to typeIds
    __commentTypeName = 'Karma.comment' #The typename of comments
    __commentTypeId = None#The typeId of the comments ('Karma.comment')
    
    def __init__(self, pipes, args):
        """
        \brief The constructor
        \param pipes The communication pipes to the PluginManager
        \param args Additional startup arguments
        """
        super(Karma, self).__init__(pipes)
    
    def initialize(self, args):
        """
        \brief The initialization
        \param args The user defined arguments (must contain 
                    database password, user, name)
        
        Creates the database structure
        """
        self.__connection = MySQLdb.connect(user = args['user'], passwd = args['password'], db = args['db'])
        #get a default cursor for database layout setup
        cursor = self.__connection.cursor()
        cursor.execute('SHOW TABLES')
        tables = [t[0] for t in cursor.fetchall()]
        
        if not 'karma_votes' in tables:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `karma_votes`
                (
                    `Id` int NOT NULL auto_increment,
                    `Vote` mediumint(7) NOT NULL default 50,
                    `FKey` int NOT NULL,
                    `FType` mediumint(5) NOT NULL,
                    `UserId` int NOT NULL,
                    `Created` datetime,
                    PRIMARY KEY(`Id`),
                    UNIQUE KEY `Target` (`FKey`, `FType`, `UserId`)
                );
            """)
        
        if not 'karma_comments' in tables:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `karma_comments`
                (
                    `Id` int NOT NULL auto_increment,
                    `Text` text,
                    `FKey` int NOT NULL,
                    `FType` int NOT NULL,
                    `UserId` int NOT NULL,
                    `Created` datetime,
                    PRIMARY KEY (`Id`)
                );
            """)
        
        if not 'karma_flags' in tables:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `karma_flags`
                (
                    `Id` int NOT NULL auto_increment,
                    `CommentId` int NOT NULL,
                    PRIMARY KEY (`Id`)
                );
            """)
            
        if not 'karma_types' in tables:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `karma_types`
                (
                    `Id` int NOT NULL auto_increment,
                    `Name` varchar(50) NOT NULL,
                    PRIMARY KEY (`Id`),
                    UNIQUE KEY `Name` (`Name`)
                );
            """)
        cursor.close()
        self.__connection.commit()
        self.__loadTypes()
        
        #enable voting/comments on comments
        self.addType(self.__commentTypeName)
        self.__commentTypeId = self.__types[self.__commentTypeName]
            
    def __getCursor(self):
        """
        \brief A helper function that returns a dict cursor to the MySQLdb
        \return The dict cursor
        """
        return self.__connection.cursor(MySQLdb.cursors.DictCursor)
    
    def __loadTypes(self):
        """
        \brief Load all karma types from the database into a local map
        """
        cursor = self.__getCursor()
        cursor.execute("SELECT Id, Name FROM `karma_types`")
        self.__types = dict([(row['Name'], int(row['Id']))for row in cursor.fetchall()])
    
    def objectTypeNameToId(self, objectTypeName):
        try:
            return self.__types[objectTypeName]
        except KeyError:
            self.log('Could not determine typeId of objectType "' + objectTypeName + '"')
            return None
    
    def addType(self, name):
        """
        \brief Adds a new object type to be voted on
        \param name The name of the new type
        \return True on success else False
        """
        if name in self.__types:
            #return false if this name is already in use
            return False
        else:
            cursor = self.__getCursor()
            cursor.execute("INSERT INTO `karma_types` (`Name`) VALUES (%s)", (name, ))
            cursor.close()
            self.__connection.commit()
            #reload the types list
            self.__loadTypes()
            return True
        
    @staticmethod    
    def voteChanged(objectType, objectKey, objectVote, userName):
        """
        \brief Signaled when a vote was changed
        \param objectType The name of the voted object class
        \param objectKey The key of the object class instance
        \param objectVote The vote that was given
        \param userName The name of the voting user
        """
        pass
    
    @staticmethod
    def karmaChanged(objectType, objectKey, karma):
        """
        \brief Signaled when the karma has changed
        \param objectType The name of the voted object class
        \param objectKey The key of the object class instance
        \param karma The new karma value
        """
        
    def changeVote(self, objectType, objectKey, objectVote, userName):
        """
        \brief Change the vote for an object (create one if there is none)
        \param objectType The typename of the object
        \param objectKey The key of the object an id of type int
        \param objectVote The actual vote, an int of range [0, 100]
        \param userName The name of the voting user
        \return True on success else False
        """
        objectTypeId = self.objectTypeNameToId(objectType)
        if objectTypeId == None:
            return False
        
        userId = self.callFunction(('Acl', 'getIdFromUserName'), userName)
        if userId == None:
            return False
        
        cursor = self.__getCursor()
        cursor.execute("""
            INSERT INTO `karma_votes` 
            (`Vote`, `FKey`, `FType`, `UserId`, `Created`) VALUES
            (%s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE `Vote` = %s, `Created` = NOW()
            """, (objectVote, objectKey, objectTypeId, userId, 
                  objectVote))
        cursor.close()
        self.__connection.commit()
        
        self.signalEvent('voteChanged', objectType, objectKey, objectVote, userName)
        self.signalEvent('karmaChanged', objectType, objectKey, self.getKarma(objectType, objectKey))
        
        return True
    
    def hasVoted(self, objectType, objectId, userName):
        """
        \brief Returns wether the user has already voted for this object
        \param objectType The typename of the object
        \param objectId The id of the object
        \param userName The name of the user whose vote should be checked
        \return True if user has voted, false if not, None if an error occured
        """
        objectTypeId = self.objectTypeNameToId(objectType)
        if objectTypeId == None:
            return None
        
        userId = self.callFunction(('Acl', 'getIdFromUserName'), userName)
        
        if userId == None:
            return None
            
        cursor = self.__getCursor()
        cursor.execute("""
            SELECT id FROM `karma_votes` WHERE
            `FKey` = %s AND
            `FTYPE` = %s AND
            `UserId` = %s 
            """, (objectId, objectTypeId, userId))
        
        if None != cursor.fetchone():
            return True
        else:
            return False
        
    def getKarma(self, objectType, objectId):
        """
        \brief Calculate the karma of the object
        \param objectType The typename of the object
        \param objectId The id of the object
        \return The karma (an integer of [0, 100]) or None in case of error
        """
        objectTypeId = self.objectTypeNameToId(objectType)
        if objectTypeId == None:
            return None
        
        cursor = self.__getCursor()
        cursor.execute("""
        SELECT AVG(`Vote`) as `karma`
        FROM `karma_votes`
        WHERE 
        `FKey` = %s AND
        `FType` = %s
        """, (objectId, objectTypeId))
        try:
            return cursor.fetchone()['karma']
        except KeyError:
            return None
    
    def getVotes(self, objectType, objectId):
        """
        \brief Get all votes of the object of type objectType with id objectId
        \param objectType The typename of the object
        \param objectId The id of the object
        \return A list of votes: [(vote, voterUserName), ...]
        """
        objectTypeId = self.objectTypeNameToId(objectType)
        if objectTypeId == None:
            return None
            
        cursor = self.__getCursor()
        cursor.execute("""
        SELECT Vote, `users`.`name` as userName FROM 
        `karma_votes` JOIN `users` ON `karma_votes`.`UserId` = `users`.`id` 
        WHERE 
        `karma_votes`.`FKey` = %s AND
        `karma_votes`.`FType` = %s
        """, (objectId, objectTypeId))
        return [(row['Vote'], row['userName']) for row in cursor.fetchall()]
    
    def getCommentTypeName(self):
        return self.__commentTypeName
        
    def getComment(self, commentId):
        """
        \brief Get one comment
        \param The id of the comment to fetch
        \return (commentId, text, userName, date, objectType, objectId) 
        """
        cursor = self.__getCursor()
        cursor.execute("""
        SELECT `Id`, `Text`, `users`.`name` as `userName`, `Created`, `karma_types`.`Name` as `Type`, `FKey`
        FROM `karma_comments` 
        JOIN `users` ON `karma_comments`.`UserId` = `users`.`id`
        JOIN `karma_types` ON `karma_comments`.`FType` = `karma_types`.`Id`
        WHERE
        `karma_comments`.`Id` = %s
        """, (commentId, ))
        comment = cursor.fetchone()
        comment = (comment['Id'], 
                   comment['Text'], 
                   comment['userName'],                   
                   comment['Created'], 
                   comment['Type'], 
                   comment['FKey'])
        return comment
    
    def addComment(self, objectType, objectId, commentText, userName, flag = False):
        """
        \brief Add a new comment to an object
        \param objectType The typename of the object
        \param objectId The id of the object
        \param commentText The text of the comment
        \param userName The name of the commenting user
        \return True on success else False
        """
        objectTypeId = self.objectTypeNameToId(objectType)
        if objectTypeId == None:
            return False
        
        userId = self.callFunction(('Acl', 'getIdFromUserName'), userName)
        if userId == None:
            return False
        
        cursor = self.__getCursor()
        
        #insert the comment
        cursor.execute("""
        INSERT INTO `karma_comments`
        (`text`, `FKey`, `FType`, `UserId`, `Created`) VALUES
        (%s, %s, %s, %s, NOW())
        """, (commentText, objectId, objectTypeId, userId))
        
        #is a flag set?
        if flag:
            cursor.execute("""
                INSERT INTO `karma_flags` 
                (`CommentId`) VALUES
                (LAST_INSERT_ID())
            """)
        
        cursor.close()
        self.__connection.commit()
        return True
    
    def editComment(self, commentId, commentText):
        """
        \brief Edit the comment with the specified id
        \param commentId The id of the comment to edit
        \param commentText The new text of the comment
        """
        cursor = self.__getCursor()
        cursor.execute("""
        UPDATE `karma_comments` SET `Text` = %s WHERE `Id` = %s
        """, (commentText, commentId))
        cursor.close()
        self.__connection.commit()
        
    def deleteComment(self, commentId):
        """
        \brief Delete the comment with the given Id
        \param commentId The id of the comment to delete
        """
        cursor = self.__getCursor()
        cursor.execute("""
        DELETE FROM `karma_comments` WHERE `Id` = %s
        """, (commentId, ))
        cursor.close()
        self.__connection.commit()
        
    def getComments(self, objectType, objectId):
        """
        \brief Get the comment hierarchy for this object
        \param objectType The typename of the object
        \param objectId The id of the object
        \return The list of comments
        [
            (id, text, user, date, [votes], [answers (other comments)]),
            ...
        ]
        """
        objectTypeId = self.objectTypeNameToId(objectType)
        if objectTypeId == None:
            return None
        
        cursor = self.__getCursor()
        cursor.execute("""
        SELECT `karma_comments`.`Id` as `Id`, `Text`, `users`.`name` as `userName`, `Created` 
        FROM `karma_comments` JOIN `users` ON `karma_comments`.`UserId` = `users`.`id`
        WHERE
        `karma_comments`.`FKey` = %s AND
        `karma_comments`.`FType` = %s  
        """, (objectId, objectTypeId))
        #get the output format
        comments = [[row['Id'], row['Text'], row['userName'], row['Created'], [], []] 
                    for row in cursor.fetchall()]
        cursor.close()
        
        for c in comments:
            c[4] = self.getVotes('Karma.comment', c[0])
            c[5] = self.__getCommentsOnComment(c[0])
            
        return comments
        
    def __getCommentsOnComment(self, commentId):
        """
        \brief Helperfunction to retrieve the comments on a comment
        \param commentId The id of the comment whose comments are to be retrieved
        \return Like getComments
        """
        cursor = self.__getCursor()
        cursor.execute("""
        SELECT Id, Text, `users`.`name` as `userName`, `Created` 
        FROM `karma_comments` JOIN `users` ON `karma_comments`.`UserId` = `users`.`id`
        WHERE
        `karma_comments`.`FKey` = %s AND
        `karma_comments`.`FType` = %s AND  
        """, (commentId, self.__commentTypeId))
        #get the output format
        comments = [(row['Id'], row['Text'], row['userName'], row['Created'], [], []) 
                    for row in cursor.fetchall()]
        cursor.close()
        
        for c in comments:
            c[4] = self.getVotes('Karma.comment', c[0])
            c[5] = self.__getCommentsOnComment(c[0])
            
        return comments
        
    def deleteFlag(self, flagId):
        """
        \brief Delete the flag with the given id
        \param flagId The id of the flag to delete
        """
        cursor = self.__getCursor()
        cursor.execute("""
        DELETE FROM `karma_comments` SET `Text` = %s WHERE `Id` = %s
        """, (flagId, ))
        cursor.close()
        self.__connection.commit()
        
    def getFlags(self, objectType = None, objectId = None):
        """
        \brief Return the flags of the object
        \param objectType The type of the object, if none is define, 
                            all flags will be returned
        \param objectId The id of the object, if none is defined, 
                        all flags of this objecttype will be returned
        \return The flag list [(id, comment, (objectId, (objectType))), ...], or None if an error occured
        
        objectType and objectId will only be returned if not given by the caller 
        """
        if objectType != None:
            objectTypeId = self.objectTypeNameToId(objectType)
            if objectTypeId == None:
                return None
           
        cursor = self.__getCursor() 
        if objectId != None:
            cursor.execute("""
            SELECT `karma_flags`.`Id` as `id`, `CommentId`
            FROM `karma_flags` JOIN `karma_comments` 
            ON `karma_flags`.`CommentId` = `karma_comments`.`Id`
            WHERE 
            `karma_comments`.`FKey` = %s AND
            `karma_comments`.`FType` = %s 
            """, (objectId, objectTypeId))
            
            return [(row['id'], self.getComments('Karma.comment', row['CommentId']))
                    for row in cursor.fetchall()]
        elif objectType != None:
            cursor.execute("""
            SELECT `karma_flags`.`Id` as `id`, `CommentId`, `karma_comments`.`FKey` as `FKey`
            FROM `karma_flags` JOIN `karma_comments` 
            ON `karma_flags`.`CommentId` = `karma_comments`.`Id`
            WHERE 
            `karma_comments`.`FType` = %s   
            """, (objectTypeId, ))
            return [(row['id'], self.getComments('Karma.comment', row['CommentId']), row['FKey'])
                    for row in cursor.fetchall()]
        else:
            cursor.execute("""
            SELECT `karma_flags`.`Id` as `id`, `CommentId`, 
            `karma_comments`.`FKey` as `FKey`, `karma_types`.`Name` as `typeName`
            FROM `karma_flags` 
            JOIN `karma_comments` 
            ON `karma_flags`.`CommentId` = `karma_comments`.`Id`
            JOIN `karma_types` ON `karma_comments`.`FType` = `karma_types`.`Id`   
            """, (objectTypeId, ))
            return [(row['id'], 
                     self.getComments('Karma.comment', row['CommentId']), 
                     row['FKey'],
                     row['typeName'])
                    for row in cursor.fetchall()]
        