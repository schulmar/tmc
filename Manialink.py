from xml.sax.saxutils import escape

class XmlElement(object):
	def __init__(self, attribs):
		self.attribs = dict([(attrib, None) for attrib in attribs])
		self.children = []
		self.content = None
	
	def addChild(self, child):
		if isinstance(child, XmlElement):
			self.children.append(child)
			return True
		else:
			return False

	def setAttr(self, attr, value):
		if attr in self.attribs:
			self.attribs[attr] = value
			return True
		else:
			return False

	def setContent(self, content):
		self.content = str(content)

	def unsetContent(self):
		self.content = None

	def getXML(self):
		xml = '<' + str(self.name)

		for key,value in self.attribs.items():
			if value != None:
				xml = xml + ' ' + str(key) + '="' + escape(str(value)) + '"'

		if len(self.children) == 0 and self.content == None:
			return  xml + '/>'

		else:
			xml = xml + '>'
			if self.content != None:
				xml = xml + escape(str(self.content))
			for child in self.children:
				xml = xml + child.getXML()

			return xml + '</' + str(self.name) + '>'
	
	def __getitem__(self, index):
		return self.attribs[index]

	def __setitem__(self, key, item):
		if key in self.attribs:
			self.attribs[key] = item
			return True
		else:
			return False

			

class Manialink(XmlElement):
	def __init__(self):
		self.name = 'manialink'
		super(Manialink, self).__init__(['id'])

displayable = ['size', 'sizen', 'pos', 'posn', 'scale']
alignable = ['valign', 'halign']  
linkable = ['url', 'manialink', 'maniazones', 'addplayerid']
formatable = ['style', 'textsize', 'textcolor']
multimedia = displayable + ['data', 'play', 'looping']
entry = displayable + alignable + formatable + ['name', 'default', 'autonewline']

class Quad(XmlElement):
	def __init__(self):
		self.name = 'quad'
		self.callback = None
		self.callback_args = None
		super(Quad, self).__init__(displayable + alignable + linkable + \
			['style', 'substyle', 'bgcolor', 'image', 'imagefocus', 'action', 'actionkey'])
	
	def setCallback(self, callback, *args):
		self.callback = callback
		self.callback_args = args

class Frame(XmlElement):
	def __init__(self):
		self.name = 'frame'
		super(Frame, self).__init__(displayable)

class Label(XmlElement):
	def __init__(self):
		self.name = 'label'
		super(Label, self).__init__(displayable + alignable + linkable + formatable + \
			['text', 'autonewline'])
	
class Format(XmlElement):
	def __init__(self):
		self.name = 'format'
		super(Format, self).__init__(formatable)

class Entry(XmlElement):
	def __init__(self):
		self.name = 'entry'
		super(Entry, self).__init__(entry)

class FileEntry(XmlElement):
	def __init__(self):
		self.name = 'fileentry'
		super(FileEntry, self).__init__(entry + ['folder'])

class Music(XmlElement):
	def __init__(self):
		self.name = 'music'
		super(Music, self).__init__(['data'])

class Audio(XmlElement):
	def __init__(self):
		self.name = 'audio'
		super(Audio, self).__init__(multimedia)

class Video(XmlElement):
	def __init__(self):
		self.name = 'video'
		super(Video, self).__init__(multimedia)

class Timeout(XmlElement):
	def __init__(self):
		self.name = 'timeout'
		super(Timeout, self).__init__([])

class Include(XmlElement):
	def __init__(self):
		self.name = 'include'
		super(Include, self).__init__(['url'])
