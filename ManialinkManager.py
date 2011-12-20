from PluginInterface import *
from Manialink import *
import random

"""
\file ManialinkManager.py
\brief Contains the ManialinkManager plugin

This plugin provides management facilities for manialinks
to abstract from the manialink scheme.
"""

class ManialinkManager(PluginInterface):
	"""
	\brief The manager class that is derived from PluginInterface
	"""
	def __init__(self, pipes, args):
		"""
		\brief The onstructor
		\param pipes The pipes for communication with the PluginManager process
		\param args The arguments for this plugin
		
		No arguments needed up to now!
		"""
		self.displays = {}
		super(ManialinkManager, self).__init__(pipes)

	def initialize(self, args):
		"""
		\brief Initializing the manager instance
		
		Connects to the serverconnector and chat for management of the manialinks and chatcommands.
		"""
		self.callMethod(('TmConnector', 'SendHideManialinkPage'))
		self.callMethod(('TmChat', 'registerChatCommand'), 'mlmanager', ('ManialinkManager', 'chat_mlmanager'))
		self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'PlayerManialinkPageAnswer', 'ManialinkAnswer')

	def chat_mlmanager(self, login, args):
		"""
		\brief The chat callback
		\param login The login of the calling player
		\param args The arguments that come from the chat input
		"""
		if args == 'clear':
			self.callMethod(('TmConnector', 'SendHideManialinkPageToLogin'), login)
			self.displays[login] = Display()
			self.callMethod(('Logger', 'log'), str(login) + ' cleared his/her ManialinkManager')

	def ManialinkAnswer(self, PlayerUid, Login, Answer, Entries):
		"""
		\brief The callback for manialink answers
		\param PlayerUid The serverside PlayerUid of the answering player
		\param Login The login of the answering player 
		\param Answer The answer number of the element pressed
		\param Entries The values of the entries in the manialink
		
		Ultimately calls the callback that was registered for this action
		"""
		a = int(Answer)
		cb = self.displays[Login].getActionCallback(a)
		entries = dict([(e['Name'], e['Value']) for e in Entries])
		self.callMethod(cb[0], entries, Login, *cb[1])

	def displayManialinkToLogin(self, DOM, mlName, login):
		"""
		\brief Display the to the player
		\param DOM The XML Tree to display
		\param mlName The name of the ManialinkPage
		\param login The login of the player which should get the Manialink
		
		The page will be managed by the manager.
		"""
		self.__insertLogin(login)
		display = self.displays[login]
		display.addManialink(DOM, mlName)
		xml = '<?xml version="1.0" encoding="utf-8" ?>' + display.getManialinkXml(mlName)
		self.callMethod(('TmConnector', 'SendDisplayManialinkPageToLogin'), login, xml, 0, False)

	def hideManialinkToLogin(self, mlName, login):
		"""
		\brief Hide the manialink 
		\param mlName The name of the manialink to hide
		\param login The login of the player on whose display the manialink should be hidden
		"""
		try:
			display = self.displays[login]
		except KeyError:
			return False
		mlid = display.removeManialink(mlName, self)
		if mlid > -1:
			xml = '<?xml version="1.0" encoding="utf-8" ?><manialink id="' + str(mlid) + '"></manialink>'
			self.callMethod(('TmConnector', 'SendDisplayManialinkPageToLogin'), login, xml, 0, False)
		

	def __insertLogin(self, login):
		"""
		\brief Add a new login to the displays list
		\param login The login to add
		
		Typically this is called on player join
		"""
		if not (login in self.displays):
			self.displays[login] = Display()

	def __removeLogin(self, login):
		"""
		\brief Remove the login from the displays list
		\param login The login to remove
		
		Typically this is called on player disconnect
		"""
		try:
			del self.logins[login]
		except KeyError:
			self.callMethod(('Logger', 'log'), 'Could not remove login ' + str(login) + ' because it is not managed')
		
		
		
class Display:
	"""
	\brief This class represents the display of one player
	"""
	def __init__(self):
		"""
		\brief Initialize the display as empty
		"""
		self.usedManialinkIds = {}
		self.ManialinkNames = {}
		self.usedActionIds = {}
		self.ManialinkIdRange = 1
		self.ActionIdRange = 1

	def addManialink(self, manialink, name):
		"""
		\brief Add a new manialink to the display
		\param manialink The manialink tree
		\param name The name of the manialink
		
		If the name is already present the old manialink will be replaced 
		"""
		if name in self.ManialinkNames:
			mlid = self.ManialinkNames[name]
			self.removeManialink(name)
		else:
			mlid = self.__getUnreservedManialinkId()
		self.usedManialinkIds[mlid] = manialink
		actionButtons = self.__getActionButtons(manialink)
		for a in actionButtons:
			self.__addAction(a)
		self.ManialinkNames[name] = mlid
		
	def getManialinkXml(self, name):
		"""
		\brief Return the xml of the manialink
		\param name The name of the manialink to retrieve
		\return The xml string or None if this name is not valid
		
		"""
		try:
			mlid = self.ManialinkNames[name]
		except KeyError:
			return None
		return '<manialink id="' + str(mlid) + '">' + self.usedManialinkIds[mlid].getXML() + '</manialink>'

	def __getUnreservedManialinkId(self):
		"""
		\brief Return a ManialinkId that is not used on this display 
		"""
		mlid = random.randint(1, self.ManialinkIdRange)
		while mlid in self.usedManialinkIds:
			mlid = random.randint(1, self.ManialinkIdRange)
			self.ManialinkIdRange += 1
		return mlid
		
	def removeManialink(self, name, mlMngr):
		"""
		\brief Remove the manialink from this display
		\param name The name of the manialink to remove
		
		This calls no replace on the server, because it should only update the local structure
		"""
		if name in self.ManialinkNames:
			mlid = self.ManialinkNames[name]
			if mlid in self.usedManialinkIds:
				ml = self.usedManialinkIds[mlid]
				actions = self.__getActionButtons(ml)
				for a in actions:
					self.__removeAction(a)
				del self.usedManialinkIds[mlid]
				del self.ManialinkNames[name]
				if not ((mlid - 1) in self.usedManialinkIds):
					self.ManialinkIdRange //= 2
					if self.ManialinkIdRange < 1:
						self.ManialinkIdRange = 1
				return mlid
			else:
				mlMngr.callMethod(('Logger', 'log'), 'Manialink id ' + str(name) + ' for name ' + str(name) + ' not found for deletion')
				return -1
		else:
			mlMngr.callMethod(('Logger', 'log'), 'Manialink name ' + str(name) + ' not found for deletion')
			return -1

	def getActionCallback(self, actionId):
		"""
		\brief Return the callback for the given actionId on this display
		\param actionId The id of the action that was pressed
		"""
		action = self.usedActionIds[int(actionId)]
		return (action.callback, action.callback_args)

	def __addAction(self, action):
		"""
		\brief Add a new action to this display
		\param action The action to add
		"""
		actionId = self.__getUnreservedActionId()
		self.usedActionIds[actionId] = action
		action['action'] = actionId

	def __getUnreservedActionId(self):
		"""
		\brief Get an actionId that is not used on this display
		"""
		aid = random.randint(1, self.ActionIdRange)	
		while aid in self.usedActionIds:
			self.ActionIdRange += 1
			aid = random.randint(1, self.ActionIdRange)
		return aid
		

	def __removeAction(self, action):
		"""
		\brief Remove an action from the list
		\param action The action to remove
		"""
		try:
			aid = int(action['action'])
			del self.usedActionIds[aid]
			if not ((aid - 1) in self.usedActionIds):
				self.ActionIdRange //= 2	
				if self.ActionIdRange < 1:
					self.ActionIdRange = 1
		except KeyError:
			self.callMethod(('Logger', 'log'), 'Could not remove action Id' + str(aid) + 'because it is not managed')

	def __getActionButtons(self, manialinkElement):
		"""
		\brief Return a list of all elements that have an action callback set
		\param manialinkElement The root element to scan
		\return The list of elements with action callback
		
		The root element and all its children are scanned for "clickable" elements,
		that define callbacks and therefore need actionids.
		"""
		actionButtons = []
		if ((isinstance(manialinkElement, Quad) or isinstance(manialinkElement, Label)) 
			and manialinkElement.callback != None):
			actionButtons.append(manialinkElement)
		if len(manialinkElement.children) > 0:
			for e in manialinkElement.children:
				actionButtons.extend(self.__getActionButtons(e))
		return actionButtons
