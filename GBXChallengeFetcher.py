import struct
import os
import xml.parsers.expat

"""
\file GBXChallengeFetcher.py
\brief Contains a class for reading gbx files
"""

class GBXChallengeFetcher:
    """
    \brief A class capable of reading GBX files
    """
    def __init__(self):
        """
        \brief Create a new Fetcher
        """
        self.fileName = ''
        self.parseXML = False
        self.tnimage = False
        self.uid = 0
        self.version = 0
        self.name = ''
        self.author = ''
        self.azone = ''
        self.type = ''
        self.envir = ''
        self.mood = ''
        self.pub = ''
        self.authortm = 0
        self.goldtm = 0
        self.silvertm = 0
        self.bronzetime = 0
        self.cost = 0
        self.multi = False
        self.unknown = None
        self.unknown2 = None
        self.unknown3 = None
        self.unknown4 = None
        self.unknown5 = None
        self.ascore = 0
        self.editor = 0
        self.password = 0
        self.xml = False
        self.parsedXML = None
        self.xmlver = None
        self.exever = 0
        self.exebld = 0
        self.lightmap = None
        self.nblaps = 0
        self.songfile = ''
        self.songurl = ''
        self.modname = ''
        self.modfile = ''
        self.modurl = ''
        self.thumbnail = None
        self.comment = ''
        self.xmlTreeRoute = []
        
    @staticmethod
    def FetchChallenge(fileName, parseXML, tnimage = False):
        """
        \brief Fetches the data about the GBX Challenge
        \param fileName The (full) path to the GBX file
        \param parseXML Should the xml be parsed
        \param tnimage Should a thumbnail be extracted from the file
        \return Save the data in the fetcher
        """
        fetcher = GBXChallengeFetcher()
        fetcher.fileName = fileName
        fetcher.parseXML = parseXML
        fetcher.tnimage = tnimage
        fetcher.getData()
        return fetcher
        
    def ReadGBXString(self, fileHandle):
        """
        \brief Reads one String (length, text) from the file
        \param fileHandle The file to read from
        \return text
        """
        strlen = struct.unpack('<L', fileHandle.read(4))[0]
        if strlen < 0 or strlen > 0x10000:
            return 'read error'
        return fileHandle.read(strlen)
    
    def startTag(self, name, attrs):
        """
        \brief Handle the begin of an xml tag
        \param name The name of the tag
        \param attrs The attributes of the tag
        """
        node = self.parsedXML 
        for step in self.xmlTreeRoute:
            node = node[step]['CHIL']
        
        if not node.has_key(name): 
            node[name] = []
            
        newNode = {}
        newNode['ATTR'] = attrs
        newNode['CHIL'] = {}
        
        node[name].append(newNode);
            
            
    def endTag(self, name):
        """
        \brief Handle the end of an xml tag
        \param Name the name of the tag
        """
        self.xmlTreeRoute.pop()
    
    def getData(self):
        """
        \brief Read the data from the file
        """
        fileHandle = open(self.fileName, 'rb')
        fileHandle.seek(0, os.SEEK_SET)
        magicGBXHeader = fileHandle.read(5)
        if magicGBXHeader != 'GBX\x06\x00':
            fileHandle.close()
            return False
        
        fileHandle.seek(4, os.SEEK_CUR)
        data = '{:08X}'.format(struct.unpack('>L', fileHandle.read(4))[0])
        if data != '003000234' and data != '00300403':
            fileHandle.close()
            return False
            
        fileHandle.seek(4, os.SEEK_CUR)
        self.version = struct.unpack('<L', fileHandle.read(4))[0]
        if self.version < 2 or self.version > 6:
            fileHandle.close()
            return False
        
        lengths = range(self.version + 1)
        for i in range(1, self.version + 1, 1):
            fileHandle.seek(4, os.SEEK_CUR)
            lengths[i] = struct.unpack('<L', fileHandle.read(4))[0]
            
        if self.version >= 5:
            lengths[4] &= 0x7FFFFFFF
            lengths[5] &= 0x7FFFFFFF
            
        #start of Times/info block
        count = ord(fileHandle.read(1))
        #skip unknown integer
        fileHandle.seek(4, os.SEEK_CUR)
        self.bronzetm = struct.unpack('<L', fileHandle.read(4))[0]
        self.silvertm = struct.unpack('<L', fileHandle.read(4))[0]
        self.goldtm = struct.unpack('<L', fileHandle.read(4))[0]
        self.authortm = struct.unpack('<L', fileHandle.read(4))[0]
        
        if self.version >= 3:
            self.cost = struct.unpack('<L', fileHandle.read(4))[0]
        
        if count >= 6:
            self.multi = (struct.unpack('<L', fileHandle.read(4))[0] != 0)
            mapType = struct.unpack('<L', fileHandle.read(4))[0]
            typeDict = {0 : 'Race', 
                        1 : 'Platform',
                        2 : 'Puzzle',
                        3 : 'Crazy',
                        4 : 'Shortcut',
                        5 : 'Stuns',
                        6 : 'Script'}
            self.type = typeDict.get(mapType, 'unknown!')
        
            if count >= 9:
                self.unknown = struct.unpack('<L', fileHandle.read(4))[0]
            if count >= 10:
                self.ascore = struct.unpack('<L', fileHandle.read(4))[0]
            if count >= 11:
                self.editor = (struct.unpack('<L', fileHandle.read(4))[0] != 0)
            if count >= 12:
                self.unknown2 = struct.unpack('<L', fileHandle.read(4))[0]
            if count >= 13:
                self.unknown4 = struct.unpack('<L', fileHandle.read(4))[0]
                self.unknown5 = struct.unpack('<L', fileHandle.read(4))[0]
        
        fileHandle.seek(4, os.SEEK_CUR)
        fileHandle.seek(5, os.SEEK_CUR)
        self.uid = self.ReadGBXString(fileHandle)
        data = struct.unpack('<L', fileHandle.read(4))[0]
        if data != 12:
            self.envir = self.ReadGBXString(fileHandle)
        else:
            self.envir = 'XML'
            
        fileHandle.seek(4, os.SEEK_CUR)
        self.author = self.ReadGBXString(fileHandle)
        self.name = self.ReadGBXString(fileHandle)
        fileHandle.seek(1, os.SEEK_CUR)
        
        if self.version >= 3:
            fileHandle.seek(4, os.SEEK_CUR)
            self.password = self.ReadGBXString(fileHandle)
            if self.password == 'read error':
                self.password = ''
                
        if self.version >= 4 and count >= 8:
            fileHandle.seek(4, os.SEEK_CUR)
            self.mood = self.ReadGBXString(fileHandle)
            fileHandle.seek(4, os.SEEK_CUR)
            if ord(fileHandle.read(4)[0]) != 3:
                self.pub = self.ReadGBXString(fileHandle)
            else:
                self.pub = ''
                
        length = 0
        for i in xrange(1, self.version + 1, 1):
            length += 8
            if i <= 3:
                length += lengths[i]
                
        fileHandle.seek(0x15 + length, os.SEEK_SET)
        
        if self.version >= 4:
            self.xml = self.ReadGBXString(fileHandle)
            self.xml = self.xml.replace('><', '>\n<')
            
        if self.version >= 5:
            fileHandle.seek(4, os.SEEK_CUR)
            thumblen = struct.unpack('<L', fileHandle.read(4))[0]
            fileHandle.seek(15, os.SEEK_CUR)
            
            if thumblen > 0 and thumblen < 0x10000:
                data = fileHandle.read(thumblen)
                
                if self.tnimage:
                    self.thumbnail = data
                    
            fileHandle.seek(16, os.SEEK_CUR)
            fileHandle.seek(10, os.SEEK_CUR)
            self.comment = self.ReadGBXString(fileHandle)
            
            if self.comment == 'read error':
                self.comment = ''
            fileHandle.seek(11, os.SEEK_CUR)
        
        fileHandle.close()
        
        
        self.parsedXML = {}
        if self.parseXML and isinstance(self.xml, str):
            parser = xml.parsers.expat.ParserCreate()
            parser.StartElementHandler = self.startTag
            parser.EndElementHandler = self.endTag
            parser.CharacterDataHandler = lambda data: None
            try:
                parser.Parse(self.xml.encode('UTF-8'))
            except Exception as e:
                self.parsedXML = e
                return False
            
            try:
                self.azone = self.parsedXML['header'][0]['CHIL']['ident'][0]['ATTR']['authorzone']
            except KeyError:
                self.azone = ''
                
            try:
                self.envir = self.parsedXML['header'][0]['CHIL']['desc'][0]['ATTR']['envir']
            except KeyError:
                self.envir = ''
                
            try:
                self.mood = self.parsedXML['header'][0]['CHIL']['desc'][0]['ATTR']['mood']
            except KeyError:
                self.mood = ''
            """
            try:
                self.xmlver = self.parsedXML['HEADER']['ATTR']['VERSION']
            except KeyError:
                self.xmlver = ''
            """ 
            try:
                self.exever = self.parsedXML['header'][0]['ATTR']['exever']
            except KeyError:
                self.exever = ''
                
            try:
                self.exebld = self.parsedXML['header'][0]['ATTR']['exebuild']
            except KeyError:
                self.exebld = ''
                
            try:
                self.respawns = self.parsedXML['header'][0]['CHIL']['times'][0]['ATTR']['respawns']
            except KeyError:
                self.respawns = ''
                
            try:
                self.stuntscore = self.parsedXML['header'][0]['CHIL']['times'][0]['ATTR']['stuntscore']
            except KeyError:
                self.stuntscore = ''
                
            try:
                self.validable = self.parsedXML['header'][0]['CHIL']['times'][0]['ATTR']['validable']
            except:
                self.validable = ''
                
            try:
                self.cpscur = self.parsedXML['header'][0]['CHIL']['checkpoints'][0]['ATTR']['cur']
                self.cpslap = self.parsedXML['header']Λ0]['CHIL']['checkpoints'][0]['ATTR']['onelap']
            except KeyError:
                self.cpscur = ''
                self.cpslap = ''
                
                    
                     
                     