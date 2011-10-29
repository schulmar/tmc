from PluginInterface import *
from Manialink import *
import random

class ManialinkManager(PluginInterface):
	def __init__(self, pipes, args):
		self.displays = {}
		super(ManialinkManager, self).__init__(pipes)

	def initialize(self, args):
		self.callMethod(('TmConnector', 'SendHideManialinkPage'))
		self.callMethod(('TmChat', 'registerChatCommand'), 'mlmanager', ('ManialinkManager', 'chat_mlmanager'))
		self.callMethod((None, 'subscribeEvent'), 'TmConnector', 'PlayerManialinkPageAnswer', 'ManialinkAnswer')

	def chat_mlmanager(self, args):
		if args[1] == 'clear':
			self.callMethod(('TmConnector', 'SendHideManialinkPageToLogin'), args[0])
			self.displays[args[0]] = Display()
			self.callMethod(('Logger', 'log'), str(args[0]) + ' cleared his/her ManialinkManager')

	def ManialinkAnswer(self, PlayerUid, Login, Answer, Entries):
		a = int(Answer)
		cb = self.displays[Login].getActionCallback(a)
		entries = dict([(e['Name'], e['Value']) for e in Entries])
		self.callMethod(cb[0], entries, Login, *cb[1])

	def displayManialinkToLogin(self, DOM, mlName, login):
		self.__insertLogin(login)
		display = self.displays[login]
		display.addManialink(DOM, mlName)
		xml = '<?xml version="1.0" encoding="utf-8" ?>' + display.getManialinkXml(mlName)
		self.callMethod(('TmConnector', 'SendDisplayManialinkPageToLogin'), login, xml, 0, False)

	def hideManialinkToLogin(self, mlName, login):
		try:
			display = self.displays[login]
		except KeyError:
			return False
		mlid = display.removeManialink(mlName)
		if mlid > -1:
			xml = '<?xml version="1.0" encoding="utf-8" ?><manialink id="' + str(mlid) + '"></manialink>'
			self.callMethod(('TmConnector', 'SendDisplayManialinkPageToLogin'), login, xml, 0, False)
		

	def __insertLogin(self, login):
		if not (login in self.displays):
			self.displays[login] = Display()

	def __removeLogin(self, login):
		try:
			del self.logins[login]
		except KeyError:
			self.callMethod(('Logger', 'log'), 'Could not remove login ' + str(login) + ' because it is not managed')
		
		
		
class Display:
	def __init__(self):
		self.usedManialinkIds = {}
		self.ManialinkNames = {}
		self.usedActionIds = {}
		self.ManialinkIdRange = 1
		self.ActionIdRange = 1

	def addManialink(self, manialink, name):
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
		try:
			mlid = self.ManialinkNames[name]
		except KeyError:
			return None
		return '<manialink id="' + str(mlid) + '">' + self.usedManialinkIds[mlid].getXML() + '</manialink>'

	def __getUnreservedManialinkId(self):
		mlid = random.randint(1, self.ManialinkIdRange)
		while mlid in self.usedManialinkIds:
			mlid = random.randint(1, self.ManialinkIdRange)
			self.ManialinkIdRange += 1
		return mlid
		
	def removeManialink(self, name):
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
				self.callMethod(('Logger', 'log'), 'Manialink id ' + str(name) + ' for name ' + str(name) + ' not found for deletion')
				return -1
		else:
			self.callMethod(('Logger', 'log'), 'Manialink name ' + str(name) + ' not found for deletion')
			return -1

	def getActionCallback(self, actionId):
		action = self.usedActionIds[int(actionId)]
		return (action.callback, action.callback_args)

	def __addAction(self, action):
		actionId = self.__getUnreservedActionId()
		self.usedActionIds[actionId] = action
		action['action'] = actionId

	def __getUnreservedActionId(self):
		aid = random.randint(1, self.ActionIdRange)	
		while aid in self.usedActionIds:
			self.ActionIdRange += 1
			aid = random.randint(1, self.ActionIdRange)
		return aid
		

	def __removeAction(self, action):
		try:
			aid = int(action['action'])
			del self.usedActionIds[aid]
			if not ((aid - 1) in self.usedActionIds):
				self.ActionIdRange //= 2	
				if self.ActionIdRange < 1:
					self.ActionIdRange = 1
		except KeyError:
			self.callMethod(('Logger', 'log'), 'Could not remove action Id' + str(mlid) + 'because it is not managed')

	def __getActionButtons(self, manialinkElement):
		list = []
		if isinstance(manialinkElement, Quad) and manialinkElement.callback != None:
			list.append(manialinkElement)
		if len(manialinkElement.children) > 0:
			for e in manialinkElement.children:
				list.extend(self.__getActionButtons(e))
		return list
