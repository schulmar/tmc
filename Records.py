from PluginInterface import *
import MySQLdb


"""
\file Records.py
\brief Contains a record management system
"""

class Records(PluginInterface):
    """
    \brief The records plugin
    
    Manage records and handle their occurence
    """
    def __init__(self, pipes, args):
        """
        \brief Create the records plugin
        \param pipes The communication pipes to the PluginManager
        \param args Additional startup arguments for the plugin
        """
        super(Records, self).__init__(pipes)
        self.__locals = [] #The local records on the current map
        self.__currentMapId = None #The database id of the current map 
        
    def initialize(self, args):
        """
        \brief Initialize the plugin
        \param args Additional startup arguments
            
        
        The args should contain 'user', 'password', 'db'
        """ 
        self.connection = MySQLdb.connect(user = args['user'], passwd = args['password'], db = args['db'])
        cursor = self.connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [i[0] for i in cursor.fetchall()]
        if 'record_times' not in tables:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `record_times`
                (
                    `id` int NOT NULL auto_increment,
                    `time` int NOT NULL,
                    `userId` int NOT NULL,
                    `mapId` int NOT NULL,
                    `rank` int NOT NULL DEFAULT '-1',
                    `updatedAt` timestamp NOT NULL,
                    PRIMARY KEY (`id`),
                    UNIQUE KEY `record` (`userId`, `mapId`)
                );
            """)
            
        self.connection.commit()
        
        self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'PlayerFinish', 'onPlayerFinish')
        self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'EndMap', 'onEndMap')
        self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'BeginMap', 'onBeginMap')
        self.callMethod(('None', 'subscribeEvent'), 'Records', 'newRecord', 'onNewRecord')
        self.__retrieveCurrentMapId()
        self.__getCurrentRecords()
        
    def __getCursor(self):
        """
        \brief A helper function that returns a dict cursor to the MySQLdb
        \return The dict cursor
        """
        return self.connection.cursor(MySQLdb.cursors.DictCursor)
    
    def __getCurrentRecords(self):
        """
        \brief Get the records for the current map from the database
        \return The records
        """
        cursor = self.__getCursor()
        cursor.execute("""
            SELECT `record_times`.*, `users`.`name` as name 
            FROM `record_times`
            JOIN `users` ON `record_times`.`userId` = `users`.`id`
            WHERE `mapId` = %s
            ORDER BY `rank` ASC
        """, (self.__currentMapId, ))
        self.__locals = cursor.fetchall()
        return self.__locals
    
    def getLocals(self):
        """
        \brief Get the local records of the current track
        \return The record list
        """
        return self.__locals
    
    def onPlayerFinish(self, PlayerUid, Login, TimeOrScore):
        """
        \brief PlayerFinish callback
        \param PlayerUid The server side uid of the finishing player
        \param Login The login of the finishing player
        \param TimeOrScore The time of the finishing player (in milliseconds?)
        """
        if TimeOrScore != 0:
            self.addRecord(Login, TimeOrScore)
                
    def addRecord(self, login, time):
        """
        \brief Add a record to the current map
        \param login The login of the player
        \param time The time of the record
        """
        mapId = self.callFunction(('Maps', 'getCurrentMapId'))
        userId = self.callFunction(('Acl', 'getIdFromUserName'), login)
        cursor = self.__getCursor()
        cursor.execute("""
            SELECT * 
            FROM `record_times`
            WHERE `userId` = %s
            AND `mapId` = %s 
        """, (userId, mapId))
        oldRecord = cursor.fetchone()
        if oldRecord == None:
            cursor.execute("""
                INSERT INTO `record_times`
                (`time`, `userId`, `mapId`, `updatedAt`)
                VALUES (%s, %s, %s, NOW())
            """, (time, userId, mapId))
            self.__updateRankingsInDatabase()
            cursor.execute("""
                SELECT *
                FROM `record_times`
                WHERE `userId` = %s AND `mapId` = %s
            """, (userId, mapId))
            newRecord = cursor.fetchone()
            self.signalEvent('newRecord', 
                             login, 
                             newRecord,
                             None)
            self.signalEvent('recordListChanged',
                             self.__getCurrentRecords())
        else:
            if oldRecord['time'] > time:
                cursor.execute("""
                    UPDATE `record_times`
                    SET `time` = %s, `updatedAt` = NOW()
                    WHERE `userId` = %s AND `mapId` = %s
                """, (time, userId, mapId))
                self.__updateRankingsInDatabase()
                cursor.execute("""
                    SELECT *
                    FROM `record_times`
                    WHERE `userId` = %s AND `mapId` = %s
                """, (userId, mapId))
                newRecord = cursor.fetchone()
                self.signalEvent('newRecord', login, newRecord, oldRecord)
                self.signalEvent('recordListChanged',
                             self.__getCurrentRecords())
                
    @staticmethod
    def newRecord(user, newRecord, oldRecord):
        """
        \brief The newRecord event signature
        \param user The login of the user that has a new record
        \param newRecord The structure of the new record
        \param oldRecord The structure of the old record or 
                None if there is no old record
        
        Record = {'time' : , 
                    'rank' : }
                    
        This signal is emitted, when a new record was driven
        """ 
        pass
    
    @staticmethod
    def recordListChanged(newList):
        """
        \brief The recordListChanged event signature
        \param newList The new list of records
        """
        pass
                
    def getRankFromRecordId(self, recordId):
        """
        \brief Return the rank of the record
        \param recordId The id of the record
        \return The rank or None if record is not known
        """
        cursor = self.__getCursor()
        cursor.execute("""
            SELECT *
            FROM `record_times`
            WHERE `id` = %s
        """, (recordId, ))
        record = cursor.fetchone()
        if record == None:
            return None
        
        cursor.execute("""
            SELECT COUNT(*) + 1 as `rank`
            FROM `record_times`
            WHERE `mapId` = %s AND
            (`time` < %s OR (`time` = %s AND `updatedAt` < %s))
        """, (record['mapId'], record['time'], record['updatedAt']))
        
        return cursor.fetchone()['rank']
    
    def onEndMap(self, Rankings, Map, WasWarmUp, MatchContinuesOnNextMap, RestartMap):
        """
        \brief EndMap callback
        \param Rankings The rankings on the current map
        \param Map The mapInfo of the ending map
        \param WasWarmUp Is this just the end of WarmUp?
        \param MatchContinuesOnNextMap ???
        \param RestartMap Will the same map be played again?
        """
        #self.__updateRankingsInDatabase()
        
    def onBeginMap(self, Map, WarmUp, MatchContinuation):
        """
        \brief BeginMap callback
        \param Map The current map struct
        \param WarmUp Is this WarmUp begin?
        \param MatchContinuation Is it a match continuation
        """
        self.__retrieveCurrentMapId()
        self.__getCurrentRecords()
        
    def __retrieveCurrentMapId(self):
        """
        \brief Retrieve the database id of the current map
        """
        self.__currentMapId = self.callFunction(('Maps', 'getCurrentMapId'))
        
    def __updateRankingsInDatabase(self):
        """
        \brief Calculate the current rankings in database
        """
        cursor = self.__getCursor()
        cursor.execute("""
            SET @row := 0;
            UPDATE `record_times`
            SET rank = @row := @row + 1
            WHERE `mapId` = %s 
            ORDER BY `time` ASC, `updatedAt` ASC
        """, (self.__currentMapId, ))
        cursor.close()
        self.connection.commit()
        
    def onRecord(self, user, newRecord, oldRecord):
        """
        \brief Display an information on new records
        """
        #nick = self.callFunction(('Players', 'getPlayerNickname'), user)
        self.callMethod(('TmConnectorn', 'SendNotice'),
                       'Gained the ' + newRecord['rank'] + '. local record' , user)