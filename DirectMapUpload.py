from PluginInterface import *
from Manialink import *
from WindowElements import *

"""
\file DirectUpload.py
\brief Contains methods for direct uploads of maps
"""

class DirectMapUpload(PluginInterface):
    """
    \class DirectMapUpload
    \brief Manage direct uploads of maps
    """
    def __init__(self, pipes, args):
        """
        \brief Create a new instance
        \param pipes The communication pipes to the PluginManager
        \param args Additional startup arguments
        """
        super(DirectMapUpload, self).__init__(pipes)
        self.__directUploadPath = 'direct_upload' #the name of the map folder for direct uploads
        
    def initialize(self, args):
        """
        \brief Initialize the instance
        \param args Additional startup arguments
        """
        self.callMethod(('Acl', 'rightAdd'), 'Maps.directMapUpload',
            'Upload maps directly to the server via HTTP connection.')
        self.callMethod(('TmChat', 'registerChatCommand'), 'upload', 
                        ('DirectMapUpload', 'chat_upload'), 
                        'Upload a map file to the server from within the game.')
        self.callMethod(('TmChat', 'registerChatCommand'), 'browse', 
                        ('DirectMapUpload', 'chat_browse'),
                        'Browse your directly uploaded maps.')
    
    def chat_upload(self, login, param):
        """
        \brief Chat callback for upload command (display upload form)
        \param login The login of the calling player
        \param param Additional params, should be ignored
        """
        if not self.callFunction(('Acl', 'userHasRight'), login, 'Maps.directMapUpload'):
            self.callFunction(('TmConnector', 'ChatSendServerMessageToLogin'), 
                            'You have insufficient rights to directly upload maps to this server!', 
                            login)
            return False
        
        frame = Frame()
        
        #the label of the submit button
        label = Label()
        label['posn'] = '19 -1'
        label['text'] = 'Upload!'
        frame.addChild(label)
        #the submit butten background
        quad = Quad()
        quad['posn'] = '18 0'
        quad['sizen'] = '9 4'
        quad['style'] = 'Bgs1'
        quad['substyle'] = 'PlayerCard'
        ml = self.callFunction(('Http', 'getUploadToken'), 
                               ('DirectMapUpload', 'directMapUpload'), 
                               login)
        quad['manialink'] = ('POST(http://' + str(ml[1][0]) + ':' + str(ml[1][1]) 
                                + '?token=' + str(ml[0]) + 
                                '&map=inputTrackFile,inputTrackFile)')
        frame.addChild(quad)
        
        #the entry
        entry = FileEntry()
        entry['posn'] = "2 -1"
        entry['sizen'] = "15 3"
        entry['name'] = "inputTrackFile"
        entry['folder'] = "Maps"
        entry['default'] = "Pick Map"
        frame.addChild(entry)
        
        w = Window('Choose map for upload')
        w.setSize((30, 10))
        w.setPos((-15, 5))
        w.addChild(frame)
        
        self.callMethod(('WindowManager', 'displayWindow'), 
                    login, 'DirectMapUpload.directMapUpload', w)
        
    def directMapUpload(self, entries, data, login):
        """
        \brief Callback for the direct http upload of maps
        \param entries The entries dict of the request (containing the filename)
        \param data The file data of the file uploaded
        \param login The login of the uploading user
        """
        #hide the upload form as the token is now expired
        self.callMethod(('ManialinkManager', 'hideManialinkToLogin'), 
                        'DirectMapUpload.directMapUpload', login)
        if self.callFunction(('Acl', 'userHasRight'), login, 
                             'DirectMapUpload.directMapUpload'):
            #get the map folder path
            mapPath = (os.path.dirname(self.callFunction(
                                    ('TmConnector', 'GetMapsDirectory')))
                        + os.path.sep)
            #get the filename
            fileName = os.path.basename(entries['map'])
            #assemble the relative path for the users map files
            relPath = self.__directUploadPath + os.path.sep + login + os.path.sep
            #create dir if not already existent
            if not os.path.isdir(mapPath + relPath):
                os.mkdir(mapPath + relPath)
            #test if this file already exists
            if os.path.isfile(mapPath + relPath + fileName):
                return """
                    <?xml version="1.0" encoding="utf-8" ?>
                    <manialink>
                        <label text="$f11$oError$o$fff: This file already exists!"/>
                    </manialink>
                    """
            #try to write the file
            try:
                mapFile = open(mapPath + relPath + fileName, "w")
                mapFile.write(data)
                mapFile.close()
            except:
                return """
                    <?xml version="1.0" encoding="utf-8" ?>
                    <manialink>
                        <label text="$f11$oError$o$fff: Could not write file. Try again later!"/>
                    </manialink>
                    """
                    
            if self.callFunction(('TmConnector', 'AddMap'), relPath + fileName):
                info = self.callFunction(('TmConnector', 'GetMapInfo'), relPath + fileName)
                return """
                <?xml version="1.0" encoding="utf-8" ?>
                <manialink>
                    <label text="Thank you for uploading this map!"/>
                </manialink>
                """
                self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
                            '$zAdded map ' + info['Name'] + ' $zto list!', login)
            else:
                os.remove(mapPath + relPath + fileName)
                return """
                <?xml version="1.0" encoding="utf-8" ?>
                <manialink>
                    <label text="Could not add map to list. Is this a map file?"/>
                </manialink>
                """
        else:
            self.callFunction(('TmConnector', 'ChatSendServerMessageToLogin'), 
                            'You have insufficient rights to directly upload maps to this server!', 
                            login)
            return """
                    <?xml version="1.0" encoding="utf-8" ?>
                    <manialink>
                        <label text="You have insufficient rights to directly upload maps to this server!"/>
                    </manialink>
                    """
                    
    def chat_browse(self, login, args):
        """
        \brief Browse the directly uploaded files
        """
        mapPath = (os.path.dirname(self.callFunction(
                                    ('TmConnector', 'GetMapsDirectory')))
                        + os.path.sep)
        personalMapPath = mapPath + self.__directUploadPath + os.path.sep + login + os.path.sep
        if not os.path.isdir(personalMapPath):
            self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'), 
                            'You do not have an upload path to browse!', 
                            login)
            return False
        
        files = os.listdir(personalMapPath)
        files.sort()
        
        mapRotationFileNames = set([i['FileName'] for i in self.callFunction(('TmConnector', 'GetMapList'), 100000, 0)])
        
        myMapsInRotation = filter(lambda i: i in mapRotationFileNames, files)
        myMapsOutRotation = filter(lambda i: i not in mapRotationFileNames, files)
        
        lines = []
        for m in myMapsOutRotation:
            line = []
            nameLabel = Label()
            nameLabel['text'] = m
            line.append(nameLabel)
            
            publishLabel = Label()
            publishLabel['text'] = 'publish'
            publishLabel.setCallback(('DirectMapUpload', 'cb_publishMap'), None, personalMapPath + m)
            line.append(publishLabel)
            
            deleteLabel = Label()
            deleteLabel['text'] = 'delete'
            deleteLabel.setCallback(('DirectMapUpload', 'cb_deleteMap'), None, personalMapPath + m)
            line.append(deleteLabel)
            
            lines.append(line)
            
        for m in myMapsInRotation:
            line = []
            nameLabel = Label()
            nameLabel['text'] = os.path.basename(m)
            line.append(nameLabel)
            
            unpublishLabel = Label()
            unpublishLabel['text'] = 'unpublish'
            unpublishLabel.setCallback(('DirectMapUpload', 'cb_unpublish'), None, m) 
            line.append(unpublishLabel)
            
            deleteLabel = Label()
            deleteLabel['text'] = 'delete'
            deleteLabel.setCallback(('DirectMapUpload', 'cb_deleteMap'), None, m)
            line.append(deleteLabel)    
            
            lines.append(line)
        
        nick = self.callFunction(('Players', 'getPlayerNickname'), login)
        window = TableWindow(nick + '$z$g\'s uploaded maps')
        window.setSize((80, 60))
        window.setPos((-40, 30))
        window.setTable(lines, 10, (20, 10, 10), ('filename', 'Maprotation', 'file'))
        
        self.callMethod(('WindowManager', 'displayWindow'), login, 'DirectMapUpload.browse', window, True)
        
    def cb_deleteMap(self, entries, login, yes, fileName):
        """
        \brief Delete the map file from disk (and remove it from the map list
        \param entries Should be empty
        \param login The login of the calling player
        \param yes Is this already confirmed
        \param fileName The file to delete
        """
        if yes == None:
            self.callMethod(('WindowManager', 'closeWindow'), {}, login, 'DirectMapUpload.browse')
            confirm = YesNoDialog('Do you really want to delete the file ' + os.path.basename(fileName))
            confirm.setAnswerCallback(('DirectMapUpload', 'cb_deleteMap'), fileName)
            confirm.setSize((40, 10))
            confirm.setPos((-20, 5))
            self.callMethod(('WindowManager', 'displayWindow'), login, 'DirectMapUpload.deleteConfirm', confirm)
            return 
        
        self.callMethod(('WindowManager', 'closeWindow'), {}, login, 'DirectMapUpload.deleteConfirm')
        if yes == True:
            myPath = (os.path.dirname(self.callFunction(
                                    ('TmConnector', 'GetMapsDirectory')))
                        + os.path.sep + self.__directUploadPath + os.path.sep
                        + login)
            if os.path.samefile(myPath, os.path.dirname(fileName)):
                self.cb_unpublishMap(entries, login, True, fileName)
                try:
                    os.remove(fileName)
                    self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
                                    'Successfully deleted file ' + 
                                    os.path.basename(fileName),
                                    login)
                except:
                    self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
                                    'Error while deleting file {} try again later'.
                                    format(os.path.basename(fileName)),
                                    login)
            else:
                pass
        else:
            pass
        
    def cb_publishMap(self, entries, login, yes, fileName):
        """
        \brief Add a map to the map rotation
        \param entries Should be empty
        \param login The login of the calling player
        \param yes Is this already confirmed
        \param fileName The file to publish
        """
        if yes == None:
            self.callMethod(('WindowManager', 'closeWindow'), {}, login, 'DirectMapUpload.browse')
            confirm = YesNoDialog('Do you really want to publish ' + os.path.basename(fileName))
            confirm.setAnswerCallback(('DirectMapUpload', 'cb_publishMap'), fileName)
            confirm.setSize((40, 10))
            confirm.setPos((-20, 5))
            self.callMethod(('WindowManager', 'displayWindow'), login, 'DirectMapUpload.publishConfirm', confirm)
            return
        
        self.callMethod(('WindowManager', 'closeWindow'), {}, login, 'DirectMapUpload.publishConfirm')
        if yes == True:
            self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
                        'Tried to publish ' + fileName, login)
        else:
            pass
        
    def cb_unpublishMap(self, entries, login, yes, fileName):
        """
        \brief Remove a map from the map rotation
        \param entries Should be empty
        \param login The login of the calling player
        \param yes Is this already confirmed
        \param fileName The file to unpublishr
        """
        if yes == None:
            self.callMethod(('WindowManager', 'closeWindow'), {}, login, 'DirectMapUpload.browse')
            confirm = YesNoDialog('Do you really want to unpublish ' + os.path.basename(fileName))
            confirm.setAnswerCallback(('DirectMapUpload', 'cb_unpublishMap'), fileName)
            confirm.setSize((40, 10))
            confirm.setPos((-20, 5))
            self.callMethod(('WindowManager', 'displayWindow'), login, 'DirectMapUpload.unpublishConfirm', confirm)
            return 
        
        self.callMethod(('WindowManager', 'closeWindow'), {}, login, 'DirectMapUpload.unpublishConfirm')
        if yes == True:
            self.callMethod(('TmConnector', 'ChatSendServerMessageToLogin'),
                        'Tried to unpublish ' + fileName, login)
        else:
            pass