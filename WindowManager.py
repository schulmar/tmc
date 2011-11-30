from PluginInterface import *
from Manialink import *
from WindowElements import *

"""
\file WindowManager.py
\brief Contains the WindowManager 
"""

class WindowManager(PluginInterface):
	"""
	\brief WindowManager class to abstract the Manialink interface
	"""
	def __init__(self, pipes, args):
		"""
		\brief Construct the WindowManager
		\param pipes The communication pipes to the PluginManager
		\param args Additional startup arguments
		"""
		self.displays = {} #The display of each player
		super(WindowManager, self).__init__(pipes)#initialize the PluginInterface

	def initialize(self, args):
		"""
		\brief Initialize the WindowManager
		\param args Should be empty
		
		Nothing to do
		"""
		pass

	def displayMl(self, *args):
		"""
		\brief Display a manialink via ManialinkManager
		\param args the arguments that would be passed to the ManialinkManager
		"""
		self.callMethod(('ManialinkManager', 'displayManialinkToLogin'), *args)

	def hideMl(self, *args):
		"""
		\brief Hide a manialink from the dipslay of a player
		\param args The args to hide a special manialink from the player
		"""
		self.callMethod(('ManialinkManager', 'hideManialinkToLogin'), *args)

	def windowFrame(self, width, height, posx, posy, posz = 0):
		"""
		\brief ???
		"""
		pass

	def closeWindow(self, entries, login, name):
		"""
		\brief Callback for closing a window
		\param entries The entries in the window's manialink
		\param login The login of the player
		\param name The name of the window to close
		"""
		try:
			display = self.displays[login]
			try:
				del display[name]
				self.hideMl(name, login)
			except KeyError:
				self.log('error: ' + str(login) + ' has no window named "' + str(name) + '" to close')
		except KeyError:
			self.log('error: login ' + str(login) + ' has no windows to be closed')

	def __addWindow(self, login, name, window, useOldState = False):
		"""
		\brief Add a window to manage
		\param login The player to display the window to
		\param name The name of the window to display
		\param window The window instance to display
		\param useOldState Should the state of the replaced window be used
		"""
		if not (login in self.displays):
			self.displays[login] = {}
		if useOldState:
			try:
				oldWindow = self.displays[login][name]
				window.setState(oldWindow.getState())
			except KeyError:
				pass
		self.displays[login][name] = window

	def displayWindow(self, login, name, window, useOldState = False):
		"""
		\brief Display the given window
		\param login The player to display the window to
		\param name The name of the window to display
		\param window The window instance to display
		\param useOldState Should be tried to use the state of the old window if there is one?
		"""
		window.setName(name)
		self.__addWindow(login, name, window, useOldState)
		ml = window.getManialink()
		self.displayMl(ml, name, login)

	def displayPagedWindow(self, login, name, title, size, pos, pages, useOldState = False):
		"""
		\brief Display a paged window
		\param login The player to display tdhe window to
		\param name The name of the window
		\param title The title of the window
		\param size The size of the window
		\param pos The upper left corner of the window
		\param pages A list of pages (manialinks)
		\param useOldState Should be tried to use the state of the old window if there is one?
		"""
		window = PagedWindow(title, pages)
		window.setName(name)
		window.setSize(size)
		window.setPos(pos)
		self.displayWindow(login, name, window, useOldState)

	def displayLinesWindow(self, login, name, title, size, pos, rows, rowsPerPage, useOldState = False):
		"""
		\brief Display lines in a window
		\param login The login of the player to display to
		\param name The name of the window
		\param size The size of the window
		\param pos The upper left corner of the window
		\param rows The rows to display
		\param rowsPerPage The number of rows to display per page
		\param useOldState Should be tried to use the state of the old window if there is one?
		"""
		window = LinesWindow(title)
		window.setName(name)
		window.setSize(size)
		window.setPos(pos)
		window.setLines(rows, rowsPerPage)
		self.displayWindow(login, name, window, useOldState)

	def displayTableWindow(self, login, name, title, size, pos, rows, rowsPerPage, 
						columnWidths, headLine = None, useOldState = False):
		"""
		\brief Display manialink elements in a table
		\param login The player to display to
		\param name The windows name
		\param title The title of the window
		\param size The size of the window
		\param pos The upper left corner of the window
		\param rows The rows to display (each is an iterable of columns)
		\param rowsPerPage The number of rows to display per page
		\param columntWidths The widths of each column
		\param headLine The headlines of each column
		\param useOldState Should be tried to use the state of the old window if there is one?
		"""
		window = TableWindow(title)
		window.setName(name)
		window.setSize(size)
		window.setPos(pos)
		window.setTable(rows, rowsPerPage, columnWidths, headLine)
		self.displayWindow(login, name, window, useOldState)

	def displayTableStringsWindow(self, login, name, title, size, pos, rows, 
								rowsPerPage, columnWidths, headLine = None, useOldState = False):
		"""
		\brief Display strings in a table
		\param login The player to display to
		\param name The windows name
		\param title The title of the window
		\param size The size of the window
		\param pos The upper left corner of the window
		\param rows The rows to display (each is an iterable of columns)
		\param rowsPerPage The number of rows to display per page
		\param columntWidths The widths of each column
		\param headLine The headlines of each column
		\param useOldState Should be tried to use the state of the old window if there is one?
		"""
		lines = []
		for r in rows:
			line = []
			i = 0
			for c in columnWidths:
				lbl = Label()
				if isinstance(r[i], unicode): 
					lbl['text'] = r[i].encode('utf-8')
				else:
					lbl['text'] = str(r[i])
				lbl['sizen'] = str(c) + ' ' + str(size[1] // rowsPerPage)
				line.append(lbl)
				i += 1		
			lines.append(line)
		self.displayTableWindow(login, name, title, size, pos, lines, 
							rowsPerPage, columnWidths, headLine, useOldState)

	#args = (windowName, pageNumber)
	def changePage(self, entries, login, name, pageNumber):
		"""
		\brief Change the page of a multiPage window
		\param entries The entries of the manialink
		\param login The login of the calling player
		\param name The name of the window
		\param pageNumber The number of the page to change to
		"""
		try:
			display = self.displays[login]
			try:
				window = display[name]
				try:
					window.setCurrentPage(pageNumber)
					self.displayMl(window.getManialink(), name, login)
				except AttributeError:
					self.log('error: ' + str(name) + ' does not seem to be a paged window')
			except KeyError:
				self.log('error: ' + str(login) + ' has no window "' + str(name) + '" to change page on')
		except KeyError:
			self.log('error: ' + str(login) + ' has no windows to change page')