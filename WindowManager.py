from PluginInterface import *
from Manialink import *


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

	def displayWindow(self, login, name, title, size, pos, content = [], closeButton = True):
		window = Window(name, title, closeButton)
		window.setSize(*size)
		window.setPos(*pos)
		for i in content:
			window.addChild(i)
		self.__addWindow(login, name, window)
		ml = window.getManialink()
		self.displayMl(ml, name, login)

	def displayPagedWindow(self, login, name, title, size, pos, pages = []):
		window = PagedWindow(name, title, pages)
		window.setSize(*size)
		window.setPos(*pos)
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

class Window(object):
	def __init__(self, name, title, closeButton = True):
		self.name = name
		self.title = title
		self.children = []
		self.setSize(10, 10)
		self.setPos(0, 0, 0)
		self.setStyle('Bgs1','BgDialogBlur')
		self.setIcon('Icons64x64_1', 'TrackInfo')
		self.closeButton = closeButton

	def setSize(self, width = None, height = None):
		if width != None:
			self.width = width
		if height != None:
			self.height = height

		
	def setPos(self, posx = None, posy = None, posz = None):
		if posx != None:
			self.posx = posx
		if posy != None:
			self.posy = posy

		if posz != None:
			self.posz = posz

	def setStyle(self, style = None, substyle = None):
		if style != None:
			self.style = style
		if substyle != None:
			self.substyle = substyle

	def setIcon(self, style = None, substyle = None, image = None):
		if style != None:
			self.iconStyle = style
		if substyle != None:
			self.iconSubstyle = substyle
		if image != None:
			self.iconImage = image

	def addChild(self, child):
		self.children.append(child)

	def setChildren(self, children):
		self.children = children

	def getManialink(self):
		#the main frame
		f = Frame()
		f['posn'] = str(self.posx) + ' ' + str(self.posy) + ' ' + str(self.posz)
		#the icon of the window
		icon = Quad()
		icon['posn'] = '0 0 2'
		icon['sizen'] = '3 3'
		icon['valign'] = 'center'
		if hasattr(self, 'iconStyle'):
			icon['style'] = self.iconStyle
			icon['substyle'] = self.iconSubstyle
		if hasattr(self, 'iconImage'):
			icon['image'] = self.iconImage
		f.addChild(icon)

		#the title bar text
		title = Label()
		title['text'] = self.title
		title['posn'] = '4 0 2'
		title['valign'] = 'center'
		title['sizen'] = str(self.width - (4 + 6)) + ' 2'
		f.addChild(title)

		#the titlebar background
		titlebg = Quad()
		titlebg['posn'] = '0 0 1'
		titlebg['valign'] = 'center'
		titlebg['sizen'] = str(self.width) + ' 5'
		titlebg['style'] = 'Bgs1'
		titlebg['substyle'] = 'BgPager'
		f.addChild(titlebg)


		if self.closeButton:
			#the close button quad
			close = Quad()
			close['style'] = 'Icons64x64_1'
			close['substyle'] = 'Close'
			close['halign'] = 'center'
			close['valign'] = 'center'
			close['sizen'] = '4 4'
			close['posn'] = str(self.width - 3) + ' 0 2'
			close.setCallback(('WindowManager', 'closeWindow'), self.name)
			f.addChild(close)
	
			#background of the closebutton
			closebg = Quad()
			closebg['halign'] = 'center'
			closebg['valign'] = 'center'
			closebg['sizen'] = '3 3'
			closebg['posn'] = str(self.width - 3) + ' 0 1' 
			closebg['style'] = 'Bgs1'
			closebg['substyle'] = 'BgCard1'
			f.addChild(closebg)

		#window background
		background = Quad()
		background['halign'] = 'top'
		background['valign'] = 'left'
		background['posn'] = '0 0 0'
		background['sizen'] = str(self.width) + ' ' + str(self.height)
		background['style'] = str(self.style)
		background['substyle'] = str(self.substyle)

		f.addChild(background)

		content = Frame()
		content['posn'] = '0 -3'
		content['sizen'] = str(self.width) + ' ' + str(self.height - 3)
		f.addChild(content)

		for c in self.children:
			content.addChild(c)

		return f

class PagedWindow(Window):
	def __init__(self, name, title, pages, page=0):
		self.pages = pages
		self.setCurrentPage(page)
		self.bigStep = 10
		super(PagedWindow, self).__init__(name, title)

	def setCurrentPage(self, page):
		self.currentPage = page
			
	def getManialink(self):
		try:
			self.setChildren(self.pages[self.currentPage])
		except IndexError:
			pass
			
		ml = super(PagedWindow, self).getManialink()

		f = Frame()
		f['posn'] = str(self.width//2) + ' ' + str(-self.height) + ' 1'
		ml.addChild(f)

		pageNumber = Label()
		pageNumber['text'] = str(1 + self.currentPage) + '/' + str(len(self.pages))
		pageNumber['sizen'] = '5 2'
		pageNumber['posn'] = '0 0 1'
		pageNumber['halign'] = 'center'
		pageNumber['valign'] = 'center'
		f.addChild(pageNumber)

		pageNumberbg = Quad()
		pageNumberbg['sizen'] = '20 3'
		pageNumberbg['posn'] = '0 0 0'
		pageNumberbg['halign'] = 'center'
		pageNumberbg['valign'] = 'center'
		pageNumberbg['style'] = 'Bgs1'
		pageNumberbg['substyle'] = 'BgPager'
		f.addChild(pageNumberbg)

		if self.currentPage > 0:
			prevPage = Quad()
			prevPage['sizen'] = '3 3'
			prevPage['posn'] = '-4 0 1'
			prevPage['valign'] = 'center'
			prevPage['halign'] = 'center'
			prevPage['style'] = 'Icons64x64_1'
			prevPage['substyle'] = 'ArrowPrev'
			prevPage.setCallback(('WindowManager','changePage'), self.name, self.currentPage - 1)
			f.addChild(prevPage)

			prevFastPage = Quad()
			prevFastPage['sizen'] = '3 3'
			prevFastPage['posn'] = '-6 0 1'
			prevFastPage['valign'] = 'center'
			prevFastPage['halign'] = 'center'
			prevFastPage['style'] = 'Icons64x64_1'
			prevFastPage['substyle'] = 'ArrowFastPrev'
			if self.currentPage > self.bigStep:
				prevFastPageNumber = self.currentPage - self.bigStep
			else:
				prevFastPageNumber = 0
			prevFastPage.setCallback(('WindowManager','changePage'), self.name, prevFastPageNumber)
			f.addChild(prevFastPage)

			firstPage = Quad()
			firstPage['sizen'] = '3 3'
			firstPage['posn'] = '-8 0 1'
			firstPage['valign'] = 'center'
			firstPage['halign'] = 'center'
			firstPage['style'] = 'Icons64x64_1'
			firstPage['substyle'] = 'ArrowFirst'
			firstPage.setCallback(('WindowManager','changePage'), self.name, 0)
			f.addChild(firstPage)

		if self.currentPage < len(self.pages) - 1:
			nextPage = Quad()
			nextPage['sizen'] = '3 3'
			nextPage['posn'] = '4 0 1'
			nextPage['valign'] = 'center'
			nextPage['halign'] = 'center'
			nextPage['style'] = 'Icons64x64_1'
			nextPage['substyle'] = 'ArrowNext'
			nextPage.setCallback(('WindowManager','changePage'), self.name, self.currentPage + 1)
			f.addChild(nextPage)

			nextFastPage = Quad()
			nextFastPage['sizen'] = '3 3'
			nextFastPage['posn'] = '6 0 1'
			nextFastPage['valign'] = 'center'
			nextFastPage['halign'] = 'center'
			nextFastPage['style'] = 'Icons64x64_1'
			nextFastPage['substyle'] = 'ArrowFastNext'
			if self.currentPage + self.bigStep < len(self.pages):
				nextFastPageNumber = self.currentPage + self.bigStep
			else:
				nextFastPageNumber = len(self.pages) - 1
			nextFastPage.setCallback(('WindowManager','changePage'), self.name, nextFastPageNumber)
			f.addChild(nextFastPage)

			lastPage = Quad()
			lastPage['sizen'] = '3 3'
			lastPage['posn'] = '8 0 1'
			lastPage['valign'] = 'center'
			lastPage['halign'] = 'center'
			lastPage['style'] = 'Icons64x64_1'
			lastPage['substyle'] = 'ArrowLast'
			lastPage.setCallback(('WindowManager','changePage'), self.name, len(self.pages) - 1)
			f.addChild(lastPage)

		return ml
		
