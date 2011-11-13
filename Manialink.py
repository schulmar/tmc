from xml.sax.saxutils import escape

"""
\file Manialink.py
\brief The file contains basic manialink classes

Some convienience classes to build a valid Manialink XML tree.
"""

class XmlElement(object):
	"""
	\brief Baseclass for each XML element
	"""
	def __init__(self, attribs):
		"""
		\brief The constructor recieves
		\params attribs All valid attribs for this element 
		"""
		self.attribs = dict([(attrib, None) for attrib in attribs])
		self.children = []
		self.content = None
	
	def addChild(self, child):
		"""
		\brief Add another XML element as child to this
		\param child The other XML element
		\return True if the element was added, False if child is not an XMLElement
		"""
		if isinstance(child, XmlElement):
			self.children.append(child)
			return True
		else:
			return False

	def setAttr(self, attr, value):
		"""
		\brief Set the attribute to the value
		\param attr The name of the attribute 
		\param value The value of the attribute
		"""
		if attr in self.attribs:
			if isinstance(value, str):
				self.attribs[attr] = value
			else:
				self.attribs[attr] = str(value)
			return True
		else:
			return False

	def setContent(self, content):
		"""
		\brief Set the content of this element
		\param content The content string
		"""
		if not isinstance(content, str):
			self.content = str(content)
		else:
			self.content = content

	def unsetContent(self):
		"""
		\brief Delete the content of this element
		"""
		self.content = None

	def getXML(self):
		"""
		\brief Get the XML string of this node
		
		The string contains of <name attribs="values"...>Content Children.getXML()</name>
		or <name attribs="values".../>
		"""
		xml = '<' + str(self.name)

		for key,value in self.attribs.items():
			if value != None:
				xml = xml + ' ' + str(key) + '="' + escape(value) + '"'

		if len(self.children) == 0 and self.content == None:
			return  xml + '/>'

		else:
			xml = xml + '>'
			if self.content != None:
				xml = xml + escape(self.content)
			for child in self.children:
				xml = xml + child.getXML()

			return xml + '</' + str(self.name) + '>'
	
	def __getitem__(self, index):
		"""
		\brief Proxy the attributes this XMLElement provides
		\param index The name of the attrib to access
		"""
		return self.attribs[index]

	def __setitem__(self, key, item):
		"""
		\brief Proxy the attributes this XMLElement provides
		\param key The attribute to set
		\param item the new value of key 
		"""
		if key in self.attribs:
			if isinstance(item, str):
				self.attribs[key] = item
			else:
				self.attribs[key] = str(item)
			return True
		else:
			return False

			

class Manialink(XmlElement):
	"""
	\brief The manialink Manialink-tag class
	
	Has its unique id, which should be set by the ManialinkManager.
	This class should only be used by the MlManager and not by any other plugin!
	"""
	def __init__(self):
		"""
		\brief Construct one manialink element
		"""
		self.name = 'manialink'
		super(Manialink, self).__init__(['id'])

displayable = ['size', 'sizen', 'pos', 'posn', 'scale']
alignable = ['valign', 'halign']  
linkable = ['url', 'manialink', 'maniazones', 'addplayerid']
formatable = ['style', 'textsize', 'textcolor']
multimedia = displayable + ['data', 'play', 'looping']
entry = displayable + alignable + formatable + ['name', 'default', 'autonewline']

class Quad(XmlElement):
	"""
	\brief The quad Manialink-tag class
	
	No children allowed!
	"""
	def __init__(self):
		"""
		\brief Construct the quad
		"""
		self.name = 'quad'
		self.callback = None
		self.callback_args = None
		super(Quad, self).__init__(displayable + alignable + linkable + \
			['style', 'substyle', 'bgcolor', 'image', 'imagefocus', 'action', 'actionkey'])
		
	def callbackInterfaceDefinition(self, entries, login, *args):
		"""
		\brief An interface definition of the callbacks that are "setCallback conform"
		\param self The instance of the PluginInterface derived class
		\param entries A dictionary that contains all entries and their values
		\param login The login of the player that answered the manialink page
		\param args The default arguments that were passed to setCallback
		
		As callbacks an only be delivered to plugins the callback method must be member
		of a PluginInterface derived class. 
		"""
		pass
	
	def setCallback(self, callback, *args):
		"""
		\brief Set a callback for clicking on this quad
		\param callback The callback destination
		\param args Preset parameters that should be applied to the callback
		"""
		self.callback = callback
		self.callback_args = args

class Frame(XmlElement):
	"""
	\brief The frame Manialink-tag class
	
	This is used for grouping and translating of its child elements 
	"""
	def __init__(self):
		"""
		\brief Construct the frame
		"""
		self.name = 'frame'
		super(Frame, self).__init__(displayable)

class Label(XmlElement):
	"""
	\brief The label Manialink-tag class
	
	A label allows textoutput. A label has no background!
	No children allowed!
	"""
	def __init__(self, text = None, callback = None, callbackArgs = ()):
		"""
		
		"""
		self.name = 'label'
		self.callback = callback
		self.callback_args = callbackArgs
		super(Label, self).__init__(displayable + alignable + linkable + formatable + \
			['text', 'autonewline', 'action'])
		self['text'] = text
		
	def setCallback(self, callback, *args):
		"""
		\brief Set a callback for clicking on this label
		\param callback The callback destination
		\param args Preset parameters that should be applied to the callback
		"""
		self.callback = callback
		self.callback_args = args
	
class Format(XmlElement):
	"""
	\brief Define a default format for each subsequent element
	
	This element does not allow any content or children
	"""
	def __init__(self):
		self.name = 'format'
		super(Format, self).__init__(formatable)

class Entry(XmlElement):
	"""
	\brief The entry Manialink-tag class
	
	Entries allow textinput from users.
	"""
	def __init__(self):
		self.name = 'entry'
		super(Entry, self).__init__(entry)

class FileEntry(XmlElement):
	"""
	\brief The fileentry Manialink-tag class
	
	Fileentries allow the userside selection of a file.
	Uploads are only possible over http/manialinks.
	In usual manialink replies this will only return the path to the file the user selected.
	"""
	def __init__(self):
		"""
		\brief Construct the fileentry
		"""
		self.name = 'fileentry'
		super(FileEntry, self).__init__(entry + ['folder'])

class Music(XmlElement):
	"""
	\brief The music Manialink-tag class
	
	Has to be embedded directly in the manialink element to work.
	Plays a background music on manialink pages. (Does not work on server-manialinks)
	"""
	def __init__(self):
		"""
		\brief Construct the music
		"""
		self.name = 'music'
		super(Music, self).__init__(['data'])

class Audio(XmlElement):
	"""
	\brief The audio Manialink-tag class
	
	Plays a sound in the Environtment noise channel of the game.
	"""
	def __init__(self):
		"""
		\brief Construct the audio
		"""
		self.name = 'audio'
		super(Audio, self).__init__(multimedia)

class Video(XmlElement):
	"""
	\brief The video Manialink-tag class
	
	Play videos on a manialink page.
	"""
	def __init__(self):
		"""
		\brief Construct the video
		"""
		self.name = 'video'
		super(Video, self).__init__(multimedia)

class Timeout(XmlElement):
	"""
	\brief The timeout Manialink-tag class
	
	Defines an interval for refetching the contents of this page.
	The value of seconds goes into content!
	"""
	def __init__(self):
		"""
		\brief Construct the timeout
		"""
		self.name = 'timeout'
		super(Timeout, self).__init__([])

class Include(XmlElement):
	"""
	\brief The include Manialink-tag class
	
	Include another resource into this page by address!
	"""
	def __init__(self):
		"""
		\brief Construct the include
		"""
		self.name = 'include'
		super(Include, self).__init__(['url'])
