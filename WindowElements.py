from Manialink import *

"""
\file WindowElements.py
\brief A file containing most of the window abstraction code

"""

class Window(object):
    """
    \brief The basic window class
    """
    
    def __init__(self, title):
        self.__closeButton = True #Should this window have a close button?
        self.__title = 'Default Title' #The title of the window
        self.__style = ('Bgs1','BgDialogBlur') #The style of this window's background
        self.__icon = ('Icons64x64_1', 'TrackInfo') #The (iconStyle, iconSubstyle) of this window
        self.__name = None #The name of this window
        self.__children = [] #The children of this window (ManialinkElements)
        self.__size = (0, 0) #The size of this window
        self.__pos = (0, 0, 0) #The position of this window

    def setName(self, name):
        """
        \brief Set the name of this window
        \param name The new name
        """
        self.__name = name

    def addChild(self, child):
        """
        \brief Add another child to the content of this window
        \param child The child to add
        """
        self.__children.append(child)

    def setTitle(self, title):
        """
        \brief Set the title caption of this window
        \param title The new title of the window
        """
        self.__title = str(title)

    def setBackgroundStyle(self, style):
        """
        \brief Set the style of the windows background quad
        \param style The new style (style, substyle)
        """
        self.__style = (str(style[0]), str(style[1]))

    def setIcon(self, iconStyle = None, iconSubstyle = None):
        """
        \brief Set the icon of the window
        \param icon The now icon
        
        Call this function without parameter to leave out the icon
        """
        self.__icon = (iconStyle, iconSubstyle)
            
    def setCloseButton(self, shouldHaveCloseButton):
        """
        \brief Define wether this window should have a close button
        \param shouldHaveCloseButton is boolean
        """
        self.__closeButton = bool(shouldHaveCloseButton)
        
    def setSize(self, size):
        """
        \brief Set the size of this window
        \param size The size should be a 2-element sized iterable of int convertibles
        """
        self.__size = (int(size[0]), int(size[1]))
        
    def setPos(self, pos):
        """
        \brief Set the position of the window
        \param pos The position should be a 2 or 3 elements sized
            iterable of int convertibles
        """
        if len(pos) == 2:
            self.__pos = (int(pos[0]), int(pos[1]), self.__pos[2])
        else:
            self.__pos = (int(pos[0]), int(pos[1]), int(pos[2]))

    def getManialink(self):
        #the main frame
        f = Frame()
        f['posn'] = str(self.__pos[0]) + ' ' + str(self.__pos[1]) + ' ' + str(self.__pos[2])
        
        if self.__icon != None:
            #the icon of the window
            icon = Quad()
            icon['posn'] = '0 0 2'
            icon['sizen'] = '3 3'
            icon['valign'] = 'center'
            if self.__icon[0] != None:
                icon['style'] = self.__icon[0]
                icon['substyle'] = self.__icon[1]
            f.addChild(icon)

        #the __title bar text
        title = Label()
        title['text'] = self.__title
        title['posn'] = '4 0 2'
        title['valign'] = 'center'
        title['sizen'] = str(self.__size[0] - (4 + 6)) + ' 2'
        f.addChild(title)

        #the titlebar background
        titlebg = Quad()
        titlebg['posn'] = '0 0 1'
        titlebg['valign'] = 'center'
        titlebg['sizen'] = str(self.__size[0]) + ' 5'
        titlebg['style'] = 'Bgs1'
        titlebg['substyle'] = 'BgPager'
        f.addChild(titlebg)


        if self.__closeButton:
            #the close button quad
            close = Quad()
            close['style'] = 'Icons64x64_1'
            close['substyle'] = 'Close'
            close['halign'] = 'center'
            close['valign'] = 'center'
            close['sizen'] = '4 4'
            close['posn'] = str(self.__size[0] - 3) + ' 0 2'
            close.setCallback(('WindowManager', 'closeWindow'), self.__name)
            f.addChild(close)
    
            #background of the closebutton
            closebg = Quad()
            closebg['halign'] = 'center'
            closebg['valign'] = 'center'
            closebg['sizen'] = '3 3'
            closebg['posn'] = str(self.__size[0] - 3) + ' 0 1' 
            closebg['style'] = 'Bgs1'
            closebg['substyle'] = 'BgCard1'
            f.addChild(closebg)

        #window background
        background = Quad()
        background['halign'] = 'top'
        background['valign'] = 'left'
        background['posn'] = '0 0 0'
        background['sizen'] = str(self.__size[0]) + ' ' + str(self.__size[1])
        background['style'] = str(self.__style[0])
        background['substyle'] = str(self.__style[1])

        f.addChild(background)

        content = Frame()
        content['posn'] = '0 -3'
        content['sizen'] = str(self.__size[0]) + ' ' + str(self.__size[1] - 3)
        f.addChild(content)

        for c in self.__children:
            content.addChild(c)

        return f

class PagedWindow(Window):
    def __init__(self, title, pages):
        """
        \brief Create a paged window
        \param title The title of the window
        \param pages The content of the pages
        """
        self.__pages = pages
        self.__bigStep = 10
        super(PagedWindow, self).__init__(title)

    def setBigStep(self, bigStep):
        """
        \brief Set the amount of pages that should be skipped by a big step
        \param bigStep The number of pages
        """
        self.__bigStep = bigStep
        

    def setCurrentPage(self, page):
        """
        \brief Set the page that should currently be displayed
        \param page The pagenumber that should be displayed
        """
        self.__currentPage = int(page)
            
    def getManialink(self):
        try:
            self.setChildren(self.__pages[self.__currentPage])
        except IndexError:
            pass
            
        ml = super(PagedWindow, self).getManialink()

        f = Frame()
        f['posn'] = str(self.__size[0]//2) + ' ' + str(-self.__size[1]) + ' 1'
        ml.addChild(f)

        pageNumber = Label()
        pageNumber['text'] = str(1 + self.__currentPage) + '/' + str(len(self.__pages))
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

        if self.__currentPage > 0:
            prevPage = Quad()
            prevPage['sizen'] = '3 3'
            prevPage['posn'] = '-4 0 1'
            prevPage['valign'] = 'center'
            prevPage['halign'] = 'center'
            prevPage['style'] = 'Icons64x64_1'
            prevPage['substyle'] = 'ArrowPrev'
            prevPage.setCallback(('WindowManager','changePage'), self.__name, self.__currentPage - 1)
            f.addChild(prevPage)

            prevFastPage = Quad()
            prevFastPage['sizen'] = '3 3'
            prevFastPage['posn'] = '-6 0 1'
            prevFastPage['valign'] = 'center'
            prevFastPage['halign'] = 'center'
            prevFastPage['style'] = 'Icons64x64_1'
            prevFastPage['substyle'] = 'ArrowFastPrev'
            if self.__currentPage > self.__bigStep:
                prevFastPageNumber = self.__currentPage - self.__bigStep
            else:
                prevFastPageNumber = 0
            prevFastPage.setCallback(('WindowManager','changePage'), self.__name, prevFastPageNumber)
            f.addChild(prevFastPage)

            firstPage = Quad()
            firstPage['sizen'] = '3 3'
            firstPage['posn'] = '-8 0 1'
            firstPage['valign'] = 'center'
            firstPage['halign'] = 'center'
            firstPage['style'] = 'Icons64x64_1'
            firstPage['substyle'] = 'ArrowFirst'
            firstPage.setCallback(('WindowManager','changePage'), self.__name, 0)
            f.addChild(firstPage)

        if self.__currentPage < len(self.__pages) - 1:
            nextPage = Quad()
            nextPage['sizen'] = '3 3'
            nextPage['posn'] = '4 0 1'
            nextPage['valign'] = 'center'
            nextPage['halign'] = 'center'
            nextPage['style'] = 'Icons64x64_1'
            nextPage['substyle'] = 'ArrowNext'
            nextPage.setCallback(('WindowManager','changePage'), self.__name, self.__currentPage + 1)
            f.addChild(nextPage)

            nextFastPage = Quad()
            nextFastPage['sizen'] = '3 3'
            nextFastPage['posn'] = '6 0 1'
            nextFastPage['valign'] = 'center'
            nextFastPage['halign'] = 'center'
            nextFastPage['style'] = 'Icons64x64_1'
            nextFastPage['substyle'] = 'ArrowFastNext'
            if self.__currentPage + self.__bigStep < len(self.__pages):
                nextFastPageNumber = self.__currentPage + self.__bigStep
            else:
                nextFastPageNumber = len(self.__pages) - 1
            nextFastPage.setCallback(('WindowManager','changePage'), self.__name, nextFastPageNumber)
            f.addChild(nextFastPage)

            lastPage = Quad()
            lastPage['sizen'] = '3 3'
            lastPage['posn'] = '8 0 1'
            lastPage['valign'] = 'center'
            lastPage['halign'] = 'center'
            lastPage['style'] = 'Icons64x64_1'
            lastPage['substyle'] = 'ArrowLast'
            lastPage.setCallback(('WindowManager','changePage'), self.__name, len(self.__pages) - 1)
            f.addChild(lastPage)

        return ml
        
