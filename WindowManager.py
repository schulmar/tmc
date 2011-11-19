from PluginInterface import *
from Manialink import *
from WindowElements import *

class WindowManager(PluginInterface):
	def __init__(self, pipes, args):
		self.displays = {}
		super(WindowManager, self).__init__(pipes)

	def initialize(self, args):
		pass

	def displayMl(self, *args):
		self.callMethod(('ManialinkManager', 'displayManialinkToLogin'), *args)

	def hideMl(self, *args):
		self.callMethod(('ManialinkManager', 'hideManialinkToLogin'), *args)

	def windowFrame(self, width, height, posx, posy, posz = 0):
		pass

	def closeWindow(self, entries, login, name):
		try:
			display = self.displays[login]
			try:
				del display[name]
				self.hideMl(name, login)
			except KeyError:
				self.log('error: ' + str(login) + ' has no window named "' + str(name) + '" to close')
		except KeyError:
			self.log('error: login ' + str(login) + ' has no windows to be closed')

	def __addWindow(self, login, name, window):
		if not (login in self.displays):
			self.displays[login] = {}
		self.displays[login][name] = window

	def displayWindow(self, login, name, window):
		window.setName(name)
		self.__addWindow(login, name, window)
		ml = window.getManialink()
		self.displayMl(ml, name, login)

	def displayPagedWindow(self, login, name, title, size, pos, pages = []):
		window = PagedWindow(title, pages)
		window.setName(name)
		window.setSize(size)
		window.setPos(pos)
		self.__addWindow(login, name, window)
		ml = window.getManialink()
		self.displayMl(ml, name, login)

	def displayLinesWindow(self, login, name, title, size, pos, rows, rowsPerPage):
		pages = []
		i = 0
		for row in rows:
			rowNumber = i % rowsPerPage
			pageNumber = i // rowsPerPage
			if rowNumber == 0:
				pages.append([])
			frame = Frame()
			frame['sizen'] = '2 %d' % (size[1] // rowsPerPage, )
			frame['posn'] = '0 -%d' % (size[1] * rowNumber/rowsPerPage, )
			for e in row:
				frame.addChild(e)
			pages[pageNumber].append(frame)
			i += 1
		self.displayPagedWindow(login, name, title, size, pos, pages)

	def displayTableWindow(self, login, name, title, size, pos, rows, rowsPerPage, 
						columnWidths, headLine = None):
		if headLine != None:
			rowsPerPage += 1
			headLineML = []
			x = 0
			for i in xrange(len(columnWidths)):
				lbl = Label()
				lbl['text'] = str(headLine[i])
				lbl['posn'] = str(x) + ' 0'
				x += columnWidths[i]
				headLineML.append(lbl)
				
		lines = []
		for r in rows:
			#insert headline on each new page
			if headLine != None and len(lines) % rowsPerPage == 0:
				lines.append(headLineML)
			line = []
			i = 0
			x = 0
			for c in columnWidths:
				r[i]['posn'] = str(x) + ' 0'
				line.append(r[i])
				x += c
				i += 1
			lines.append(line)
		self.displayLinesWindow(login, name, title, size, pos, lines, rowsPerPage)

	def displayTableStringsWindow(self, login, name, title, size, pos, rows, rowsPerPage, columnWidths, headLine = None):
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
		self.displayTableWindow(login, name, title, size, pos, lines, rowsPerPage, columnWidths, headLine)

	#args = (windowName, pageNumber)
	def changePage(self, entries, login, name, pageNumber):
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