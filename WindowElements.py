from Manialink import *

"""
\file WindowElements.py
\brief A file containing most of the window abstraction code

"""

class Widget(object):
    """
    \brief An abstract basic widget class
    """
    def __init__(self):
        """
        \brief Initialize the widgets members
        """
        self.__name = None #The name of this widget
        self.__size = (0, 0) #The widgets size
        self.__pos = (0, 0, 0) #The widgets position
        self.__user = None #The name of the user to display to
        self.__windowManager = None #The WindowManager instance that handles this window
        
    def getName(self):
        """
        \brief Return the name of the window
        \return The name of the window
        """
        return self.__name

    def setName(self, name):
        """
        \brief Set the name of this window
        \param name The new name
        """
        self.__name = name
        
    def getSize(self):
        """
        \brief Get the widgets size
        \return (width, height)
        """
        return self.__size
    
    def setSize(self, size):
        """
        \brief Set the widgets size
        \param Size The new size, should be (int, int)
        """
        self.__size = (int(size[0]), int(size[1]))
    
    def getPos(self):
        """
        \brief Return the widgets position
        \return (x, y, z)
        """
        return self.__pos
        
    def setPos(self, pos):
        """
        \brief Set the widgets position
        \param pos The new position, either (x, y) or (x, y, z)
        """
        if len(pos) == 2:
            self.__pos = (int(pos[0]), int(pos[1]), self.__pos[2])
        else:
            self.__pos = (int(pos[0]), int(pos[1]), int(pos[2]))
            
    def getUser(self):
        """
        \brief Return the user of this widget
        \return The name of the user
        """
        return self.__user
    
    def setUser(self, name):
        """
        \brief Set the name of the user that sees this window
        \param name
        """
        self.__user = name
            
    def getWindowManager(self):
        """
        \brief Get the WindowManager instance that handles this window
        \return The instance
        """
        return self.__windowManager
    
    def setWindowManager(self, wm):
        """
        \brief Set the WindowManager instance that handles this window
        \param wm The WindowManager
        """
        self.__windowManager = wm
        
    def getManialink(self):
        """
        \brief Get the manialink elements of this window
        """
        pass
    
    def getState(self):
        """
        \brief Get the current state of this window
        """
        pass
    
    def setState(self, state):
        """
        \brief Set the current state of this window
        \param state A former, saved state
        """
        pass
            
class YesNoDialog(Widget):
    """
    \brief A dialog that displays a question to the user, 
            that can be answered with yes and no.
    """       
    def __init__(self, question):
        """
        \brief Initialize the dialog with the question to ask
        """     
        super(YesNoDialog, self).__init__()
        self.__question = question
        self.__callback = None
        self.__callbackArgs = None
    
    @staticmethod
    def answerCallbackSignature(entries, login, yesNo, *args):
        """
        \brief The signature of the answer callback
        \param entries Should be empty
        \param login The login of the calling player
        \param yesNo Was yes(True) or no(False) clicked
        \param *args Additional arguments that were defined at setAnswerCallback
        """    
        
    def setAnswerCallback(self, callback, *args):
        """
        \brief Set the callback
        \param callback The new callback
        \param args Additional arguments that should be passed to the callback
        """
        self.__callback = callback
        self.__callbackArgs = args
        
    def getManialink(self):
        """
        \brief Get the manialink of this window
        """
        pos = self.getPos()
        size = self.getSize()

        mainFrame = Frame()
        mainFrame['posn'] = '{:d} {:d} {:d}'.format(pos[0], pos[1], pos[2])
        
        bodyBgQuad = Quad()
        bodyBgQuad['sizen'] = '{:d} {:d}'.format(*size)
        bodyBgQuad['posn'] = '0 0 -1'
        bodyBgQuad['style'] = 'Bgs1'
        bodyBgQuad['substyle'] = 'BgWindow1'
        mainFrame.addChild(bodyBgQuad)
        
        questionLabel = Label()
        questionLabel['text'] = self.__question
        questionLabel['sizen'] = '{:d} {:d}'.format(size[0] - 2, size[1] - 5)
        questionLabel['posn'] = '1 -1'
        mainFrame.addChild(questionLabel)
        
        yesButton = Label()
        yesButton['text'] = 'Yes'
        yesButton['sizen'] = '5 2'
        yesButton['posn'] = '2 -{:d}'.format(size[1] - 5)
        yesButton.setCallback(self.__callback, True, *self.__callbackArgs)
        mainFrame.addChild(yesButton)
        
        noButton = Label ()
        noButton['text'] = 'No'
        noButton['sizen'] = '5 2'
        noButton['posn'] = '8 -{:d}'.format(size[1] - 5)
        noButton.setCallback(self.__callback, False, *self.__callbackArgs)
        mainFrame.addChild(noButton)
        
        return mainFrame 
        
class CommentInput(Widget):
    """
    \brief A comment input dialog
    
    This expects a callback which will get called on submit.
    The text is in the enty with name commentTex
    """
    def __init__(self, callback, callbackArgs, title, text = 'Enter your comment here!'):
        """
        \brief Construct the CommentInput
        \param callback The function that will get called on submit
        \param callbackArgs Additional arguments that should be passed 
            to the callback
        \param title The title of the dialog
        \param text The initial text of the entry
        """
        super(CommentInput, self).__init__()
        self.__callback = callback #The submit-callback
        self.__callbackArgs = callbackArgs #the additional arguments to the callback function
        self.__title = title #The title of the window
        self.__text = text #The initial text of the enty
        
    def getManialink(self):
        """
        \brief Get the manialink hierarchie
        """
        pos = self.getPos()
        size = self.getSize()

        mainFrame = Frame()
        mainFrame['posn'] = '{:d} {:d} {:d}'.format(pos[0], pos[1], pos[2])

        bodyBgQuad = Quad()
        bodyBgQuad['sizen'] = '{:d} {:d}'.format(*size)
        bodyBgQuad['posn'] = '0 0 -1'
        bodyBgQuad['style'] = 'Bgs1'
        bodyBgQuad['substyle'] = 'BgWindow1'
        mainFrame.addChild(bodyBgQuad)

        titleBgQuad = Quad()
        titleBgQuad['sizen'] = '{:d} {:d}'.format(size[0], 6)
        titleBgQuad['style'] = 'Bgs1'
        titleBgQuad['substyle'] = 'BgTitle2'
        mainFrame.addChild(titleBgQuad)

        titleLabel = Label()
        titleLabel['text'] = self.__title
        titleLabel['posn'] = '2 -2 1'
        titleLabel['sizn'] = '{:d} {:d}'.format(size[0] - 4, size[1] - 1)
        mainFrame.addChild(titleLabel)
        """
        entryBgQuad = Quad()
        entryBgQuad['bgcolor'] = '0009'
        entryBgQuad['sizen'] = '{:d} {:d}'.format(size[0] - 4, size[1] - 10)
        entryBgQuad['posn'] = '2 -8 0'
        mainFrame.addChild(entryBgQuad)
        """     
        entry = Entry()
        entry['posn'] = '2 -8 1'
        entry['sizen'] = '{:d} {:d}'.format(size[0] - 4, size[1] - 20)
        entry['autonewline'] = '1'
        entry['default'] = self.__text
        entry['name'] = 'commentText'
        entry['focusareacolor1'] = '0009'
        entry['focusareacolor2'] = '000F'
        mainFrame.addChild(entry)

        cancelButtonBgQuad = Quad()
        cancelButtonBgQuad['posn'] = '{:d} {:d} 1'.format(4, 8 - size[1])
        cancelButtonBgQuad['sizen'] = '10 4'
        cancelButtonBgQuad['style'] = 'Bgs1'
        cancelButtonBgQuad['substyle'] = 'BgButton'
        cancelButtonBgQuad.setCallback(('WindowManager', 'closeWindow'), self.getName())
        mainFrame.addChild(cancelButtonBgQuad)
        
        cancelButtonLabel = Label()
        cancelButtonLabel['posn'] = '{:d} {:d} 2'.format(5, 7 - size[1])
        cancelButtonLabel['sizen'] = '8 3'
        cancelButtonLabel['text'] = 'Cancel'
        cancelButtonLabel.setCallback(('WindowManager', 'closeWindow'), self.getName())
        mainFrame.addChild(cancelButtonLabel)
        
        submitButtonBgQuad = Quad()
        submitButtonBgQuad['halign'] = 'right'
        submitButtonBgQuad['posn'] = '{:d} {:d} 1'.format(size[0] - 4, 8 - size[1])
        submitButtonBgQuad['sizen'] = '10 4'
        submitButtonBgQuad['style'] = 'Bgs1'
        submitButtonBgQuad['substyle'] = 'BgButton'
        submitButtonBgQuad.setCallback(self.__callback, *self.__callbackArgs)
        mainFrame.addChild(submitButtonBgQuad)
        
        submitButtonLabel = Label()
        submitButtonLabel['halign'] = 'right'
        submitButtonLabel['posn'] = '{:d} {:d} 2'.format(size[0] - 6, 7 - size[1])
        submitButtonLabel['sizen'] = '8 3'
        submitButtonLabel['text'] = 'Submit'
        submitButtonLabel.setCallback(self.__callback, *self.__callbackArgs)
        mainFrame.addChild(submitButtonLabel)

        return mainFrame

class Window(Widget):
    """
    \brief The basic window class
    """
    
    def __init__(self, title):
        super(Window, self).__init__()
        self.__closeButton = True #Should this window have a close button?
        self.__title = title #The title of the window
        self.__style = ('Bgs1','BgDialogBlur') #The style of this window's background
        self.__icon = ('Icons64x64_1', 'TrackInfo') #The (iconStyle, iconSubstyle) of this window
        self.__children = [] #The children of this window (ManialinkElements)

    def addChild(self, child):
        """
        \brief Add another child to the content of this window
        \param child The child to add
        """
        self.__children.append(child)
        
    def setChildren(self, newChildren):
        """
        \brief Overwrite the children list with a new one
        \param newChildren The new children list
        """
        self.__children = newChildren

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

    def getManialink(self):
        #the main frame
        f = Frame()
        
        size = self.getSize()
        pos = self.getPos()
        
        f['posn'] = str(pos[0]) + ' ' + str(pos[1]) + ' ' + str(pos[2])
        
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
        title['sizen'] = str(size[0] - (4 + 6)) + ' 2'
        f.addChild(title)

        #the titlebar background
        titlebg = Quad()
        titlebg['posn'] = '0 0 1'
        titlebg['valign'] = 'center'
        titlebg['sizen'] = str(size[0]) + ' 5'
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
            close['posn'] = str(size[0] - 3) + ' 0 2'
            close.setCallback(('WindowManager', 'closeWindow'), self.getName())
            f.addChild(close)
    
            #background of the closebutton
            closebg = Quad()
            closebg['halign'] = 'center'
            closebg['valign'] = 'center'
            closebg['sizen'] = '3 3'
            closebg['posn'] = str(size[0] - 3) + ' 0 1' 
            closebg['style'] = 'Bgs1'
            closebg['substyle'] = 'BgCard1'
            f.addChild(closebg)

        #window background
        background = Quad()
        background['halign'] = 'top'
        background['valign'] = 'left'
        background['posn'] = '0 0 0'
        background['sizen'] = str(size[0]) + ' ' + str(size[1])
        background['style'] = str(self.__style[0])
        background['substyle'] = str(self.__style[1])

        f.addChild(background)

        content = Frame()
        content['posn'] = '0 -3'
        content['sizen'] = str(size[0]) + ' ' + str(size[1] - 3)
        f.addChild(content)

        for c in self.__children:
            content.addChild(c)

        return f

class PagedWindow(Window):
    def __init__(self, title, pages = []):
        """
        \brief Create a paged window
        \param title The title of the window
        \param pages The content of the pages
        """
        super(PagedWindow, self).__init__(title)
        self.__pages = pages #The list of pages
        self.__bigStep = 10 #The number of pages to skip on a big step
        self.__currentPage = 0 #The currently displayed page

    def setBigStep(self, bigStep):
        """
        \brief Set the amount of pages that should be skipped by a big step
        \param bigStep The number of pages
        """
        self.__bigStep = bigStep
        
    def getCurrentPageIndex(self):
        """
        \brief Return the index of the current page
        \return The index of the current page
        """
        return self.__currentPage

    def setCurrentPage(self, page):
        """
        \brief Set the page that should currently be displayed
        \param page The pagenumber that should be displayed
        """
        self.__currentPage = int(page)
            
    def setPages(self, pages):
        """
        \brief Set the pages of this window
        \param pages The new pages
        """
        self.__pages = pages
            
    def getManialink(self):
        try:
            self.setChildren(self.__pages[self.__currentPage])
        except IndexError:
            pass
            
        ml = super(PagedWindow, self).getManialink()

        size = self.getSize()
        name = self.getName()

        f = Frame()
        f['posn'] = str(size[0]//2) + ' ' + str(-size[1]) + ' 1'
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
            prevPage.setCallback(('WindowManager','changePage'), name, self.__currentPage - 1)
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
            prevFastPage.setCallback(('WindowManager','changePage'), name, prevFastPageNumber)
            f.addChild(prevFastPage)

            firstPage = Quad()
            firstPage['sizen'] = '3 3'
            firstPage['posn'] = '-8 0 1'
            firstPage['valign'] = 'center'
            firstPage['halign'] = 'center'
            firstPage['style'] = 'Icons64x64_1'
            firstPage['substyle'] = 'ArrowFirst'
            firstPage.setCallback(('WindowManager','changePage'), name, 0)
            f.addChild(firstPage)

        if self.__currentPage < len(self.__pages) - 1:
            nextPage = Quad()
            nextPage['sizen'] = '3 3'
            nextPage['posn'] = '4 0 1'
            nextPage['valign'] = 'center'
            nextPage['halign'] = 'center'
            nextPage['style'] = 'Icons64x64_1'
            nextPage['substyle'] = 'ArrowNext'
            nextPage.setCallback(('WindowManager','changePage'), name, self.__currentPage + 1)
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
            nextFastPage.setCallback(('WindowManager','changePage'), name, nextFastPageNumber)
            f.addChild(nextFastPage)

            lastPage = Quad()
            lastPage['sizen'] = '3 3'
            lastPage['posn'] = '8 0 1'
            lastPage['valign'] = 'center'
            lastPage['halign'] = 'center'
            lastPage['style'] = 'Icons64x64_1'
            lastPage['substyle'] = 'ArrowLast'
            lastPage.setCallback(('WindowManager','changePage'), name, len(self.__pages) - 1)
            f.addChild(lastPage)

        return ml
    
    def getState(self):
        """
        \brief Get the current state of the window
        \return The state dictionary
        """
        return {'currentPage' : self.__currentPage}
        
    def setState(self, state):
        try:
            newCPage = state['currentPage']
            if newCPage < 0:
                self.__currentPage = 0
            elif newCPage >= len(self.__pages):
                self.__currentPage = len(self.__pages) - 1
            else:
                self.__currentPage = newCPage
        except KeyError:
            return
        
class LinesWindow(PagedWindow):
    """
    \brief Defines a PagedWindow in lines
    """

    def setLines(self, lines, linesPerPage):
        """
        \brief Set the lines of this window, defining the pages
        \param lines A list of a list of manialinkElements, one per line
        """        
        pages = []
        i = 0
        size = self.getSize()
        #correct the size as header is already used
        size = (size[0], size[1] - 8) 
        for row in lines:
            rowNumber = i % linesPerPage
            pageNumber = i // linesPerPage
            if rowNumber == 0:
                pages.append([])
            frame = Frame()
            frame['sizen'] = '2 {:d}'.format(size[1] // linesPerPage)
            frame['posn'] = '0 -{:d}'.format(size[1] * rowNumber/linesPerPage)
            for e in row:
                frame.addChild(e)
            pages[pageNumber].append(frame)
            i += 1
        self.setPages(pages)
        
class TableWindow(LinesWindow):
    """
    \brief A window in which content is ordered in rows and columns on 
        multiple pages
    """
    def setTable(self, rows, linesPerPage, columnWidths, headLine = None):
        """
        \brief Create the table from the input data
        \param rows A list of columns (each field is a list of ManialinkElements)
        \param linesPerPage The number of lines to display per page
        \param columnWidths The width for each column of the table
        \param headLine The headline for the table
        """
        if headLine != None:
                linesPerPage += 1
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
            if headLine != None and len(lines) % linesPerPage == 0:
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
        self.setLines(lines, linesPerPage)
        
class TableStringsWindow(TableWindow):
    def setTableStrings(self, strings, linesPerPage, columnWidths, headLine = None):
        """
        \brief Create the table from the input data
        \param rows A list of columns (each field is a list of ManialinkElements)
        \param linesPerPage The number of lines to display per page
        \param columnWidths The width for each column of the table
        \param headLine The headline for the table
        """
        lines = []
        size = self.getSize()
        for r in strings:
            line = []
            i = 0
            for c in columnWidths:
                lbl = Label()
                if isinstance(r[i], unicode): 
                    lbl['text'] = r[i].encode('utf-8')
                else:
                    lbl['text'] = str(r[i])
                lbl['sizen'] = str(c) + ' ' + str(size[1] // linesPerPage)
                line.append(lbl)
                i += 1        
            lines.append(line)
        self.setTable(lines, linesPerPage, columnWidths, headLine)
        
class CommentOutput(PagedWindow):
    """
    \brief Prints some comments on the screen
    """
    def __init__(self, title):
        """
        \brief Create a paged window with the comments
        \param title The title of the window
        \param comments The comments as given by Karma.getComments
        """
        super(CommentOutput, self).__init__(title)
        
        self.__commentVoteCallback = None #The callback on comment votes
        self.__commentEditCallback = None #The callback for editing comments
        self.__commentDeleteCallback = None #The callback for deleting comments
        self.__commentAnswerCallback = None #The callback for answering to comments
        
        self.setPages([])
        
    @staticmethod
    def commentVoteCallbackSignature(entries, login, commentId, vote):
        """
        \brief The commentVoteCallback signature
        \param entries The entries, should be emtpy
        \param login The login of the invoking player
        \param commentId The id of the comment voted an
        \param vote The vote value
        """
        pass
        
    def setCommentVoteCallback(self, callback):
        """
        \brief Set the comment vote callback
        \param callback The new callback
        """
        self.__commentVoteCallback = callback
    
    @staticmethod
    def commentEditCallbackSignature(entries, login, commentId):
        """
        \brief The commentEditCallback signature
        \param entries Should be empty
        \param login The login of the invoking player
        \param commentId The id of the comment to edit
        """
        pass
    
    def setCommentEditCallback(self, callback):
        """
        \brief Set the new comment edit callback (invoked on clicking edit)
        \param callback The new callback
        """
        self.__commentEditCallback = callback
    
    @staticmethod
    def commentDeleteCallbackSignature(entries, login, commentId):
        """
        \brief The signature of the commentDeleteCallback
        \param entries Should be empty
        \param login The login of the invoking player
        \param commentId The id of the comment to delete
        """
        pass
    
    def setCommentDeleteCallback(self, callback):
        """
        \brief Set the new commentDeleteCallback
        \param callback The new callback
        """
        self.__commentDeleteCallback = callback
        
    @staticmethod
    def commentAnswerCallbackSignature(entries, login, aswerToCommentId):
        """
        \brief The signature of the commentAnswerCallback
        \param entries Should be empty
        \param login The login of the calling player
        \param answerToCommentId The id of the comment to answer to
        """
        pass
    
    def setCommentAnswerCallback(self, callback):
        """
        \brief Set the answer callback
        \param callback the new answer callback0
        """
        self.__commentAnswerCallback = callback
    def setComments(self, comments):
        manialinks = []
        page = []
        size = self.getSize()
        consumedHeight = 0
        for c in comments:
            (ml, height) = self.__getCommentMl(c)
            if size[1] < consumedHeight + height:
                manialinks.append(page)
                page = []
                consumedHeight = 0
            heightFrame = Frame()
            heightFrame['posn'] = '0 {:d}'.format(-consumedHeight)
            heightFrame.addChild(ml)
            consumedHeight += height
            page.append(heightFrame)
        manialinks.append(page)
        self.setPages(manialinks)
    
    def __getCommentMl(self, comment):
        """
        \brief Setup the Manialink for one comment
        \param comment Expected {depth, height, karma, votable, editable, deletable, answerable, nickName, commentTuple}
        \return The manialink toplevel frame
        """
        deleted = comment['commentTuple'][6]
        indent = comment['depth']
        width = self.getSize()[0] - indent
        head = 6
        foot = 6
        if deleted:
            height = 0
        else:
            height = 3 * max([len(comment['commentTuple'][1]) // width, 1])
        
        consumedHeight = 0
        
        commentFrame = Frame()
        commentFrame['posn'] = '{:d} {:d}'.format(indent, 0)
        
        commentBgQuad = Quad()
        commentBgQuad['posn'] = '1 0'
        commentBgQuad['sizen'] = '{:d} {:d}'.format(width - 2, height + head + foot)
        consumedHeight += height + head + foot
        commentBgQuad['style'] = 'Bgs1'
        commentBgQuad['substyle'] = 'BgWindow1'
        commentFrame.addChild(commentBgQuad)
        
        headBarBgQuad = Quad()
        headBarBgQuad['sizen'] = '{:d} {:d}'.format(width - 2, 6)
        headBarBgQuad['posn'] = '1 0 1'
        headBarBgQuad['style'] = 'Bgs1'
        headBarBgQuad['substyle'] = 'BgTitle3'
        commentFrame.addChild(headBarBgQuad)
        
        nameLabel = Label()
        nameLabel['text'] = comment['nickName']
        nameLabel['posn'] = '4 -2 2'
        nameLabel['sizen'] = '{:d} {:d}'.format(width // 2 - 2, 2)
        commentFrame.addChild(nameLabel)
        
        votesFrame = Frame()
        votesFrame['posn'] = '{:d} {:d} 1'.format(width - 16, -3)
        commentFrame.addChild(votesFrame)
        
        if (comment['votable'] and not deleted 
            and self.__commentVoteCallback != None):
            voteDown = Quad()
            voteDown['valign'] = 'center'
            voteDown['posn'] = '0 0 1'
            voteDown['sizen'] = '5 5'
            voteDown['style'] = 'Icons64x64_1'
            voteDown['substyle'] = 'ArrowDown'
            voteDown.setCallback(self.__commentVoteCallback, comment['commentTuple'][0], 0)
            votesFrame.addChild(voteDown)
        
        karmaLabel = Label()
        karmaLabel['valign'] = 'center'
        karmaLabel['text'] = '{:d}% ({:d})'.format(comment['karma'], len(comment['commentTuple'][4]))
        karmaLabel['posn'] = '{:d} {:d} 1'.format(6, 0)
        karmaLabel['sizen'] = '4 2'
        votesFrame.addChild(karmaLabel)
        
        if (comment['votable'] and not deleted
            and self.__commentVoteCallback != None):
            voteUp = Quad()
            voteUp['valign'] = 'center'
            voteUp['posn'] = '9 0 1'
            voteUp['sizen'] = '5 5'
            voteUp['style'] = 'Icons64x64_1'
            voteUp['substyle'] = 'ArrowUp'
            voteUp.setCallback(self.__commentVoteCallback, comment['commentTuple'][0], 100)
            votesFrame.addChild(voteUp)
        
        textLabel = Label()
        textLabel['text'] = ' '.join(comment['commentTuple'][1].split('\n'))
        textLabel['sizen'] = '{:d} {:d}'.format(width - 2, height)
        textLabel['posn'] = '2 -6 1'
        textLabel['autonewline'] = '1'
        commentFrame.addChild(textLabel)
        
        footBarFrame = Frame()
        footBarFrame['posn'] = '{:d} {:d} 1'.format(1, 2 - (height + 14))
        commentFrame.addChild(footBarFrame)
        
        footBarBgQuad = Quad()
        footBarBgQuad['sizen'] = '{:d} {:d}'.format(width - 2, 6)
        footBarBgQuad['valign'] = 'bottom'
        footBarBgQuad['style'] = 'Bgs1'
        footBarBgQuad['substyle'] = 'BgTitle2'
        footBarFrame.addChild(footBarBgQuad)
     
        dateLabel = Label()
        dateLabel['text'] = comment['commentTuple'][3]
        dateLabel['valign'] = 'center'
        dateLabel['posn'] = '2 3'
        dateLabel['sizen'] = '{:d} {:d}'.format(width // 2, 3)
        footBarFrame.addChild(dateLabel)
        
        if not deleted:
            if comment['answerable'] and self.__commentAnswerCallback != None:
                answerButtonLabel = Label()
                answerButtonLabel['text'] = 'Answer'
                answerButtonLabel['valign'] = 'bottom'
                answerButtonLabel['posn'] = '{:d} {:d} 1'.format(width - 10, 1)
                answerButtonLabel['sizen'] = '9 4'
                answerButtonLabel['focusareacolor1'] = '0000'
                answerButtonLabel.setCallback(self.__commentAnswerCallback, comment['commentTuple'][0])
                footBarFrame.addChild(answerButtonLabel)
            
            if comment['editable'] and self.__commentEditCallback != None:
                editButtonLabel = Label()
                editButtonLabel['text'] = 'Edit'
                editButtonLabel['valign'] = 'bottom'
                editButtonLabel['posn'] = '{:d} {:d} 1'.format(width - 20, 1)
                editButtonLabel['sizen'] = '9 4'
                editButtonLabel['focusareacolor1'] = '000F'
                editButtonLabel.setCallback(self.__commentEditCallback, comment['commentTuple'][0])
                footBarFrame.addChild(editButtonLabel)
                
            
            if comment['deletable'] and self.__commentDeleteCallback != None:
                deleteButtonLabel = Label()
                deleteButtonLabel['text'] = 'Delete'
                deleteButtonLabel['valign'] = 'bottom'
                deleteButtonLabel['posn'] = '{:d} {:d} 1'.format(width - 30, 1)
                deleteButtonLabel['sizen'] = '9 4'
                deleteButtonLabel['focusareacolor1'] = '000F'
                deleteButtonLabel.setCallback(self.__commentDeleteCallback, comment['commentTuple'][0])
                footBarFrame.addChild(deleteButtonLabel)
            
        return (commentFrame, consumedHeight)
    
class RightsWindow(TableWindow):
    def __init__(self, title):
        """
        \brief Initialize rights window
        \param title The title of the window
        """
        super(RightsWindow, self).__init__(title)
        self.__setRightCallback = None #The callback for setting a specific right
        self.__setRightCallbackArgs = None #Additional arguments for the callback
        self.__editable = False #Should this right list be editable (clickable)
        
    @staticmethod
    def setRightCallbackSignature(entries, login, rightName, value, *userArgs):
        """
        \brief The signature of the rightCallback
        \param entries Should be emtpy
        \param login The login of the managing player
        \param rightName The name of the right to change
        \param value The value to change the right to
        \param *userArgs Additional arguments defined by setRightCallback
        """
        
    def setSetRightCallback(self, callback, args = ()):
        """
        \brief Set the setRightCallback and its args
        \param callback The new callback
        \param args Userdefined arguments to the callback
        """
        self.__setRightCallback = callback
        self.__setRightCallbackArgs = args
        
    def setEditable(self, editable):
        """
        \brief Set wether the rights should be editable
        \param editable Defines wether the list should be editable
        """
        self.__editable = editable
        
    def setRights(self, rights):
        """
        \brief Set content of the window
        \param rights The list of rights of (rightName, description, hasRight)
        """
        rows = []
        size = self.getSize()
        buttonSize = 10
        nameSize = 0.3
        descriptionSize = 1 - nameSize 
        
        for right in rights:
            row = []
            rightEnabled = Quad()
            rightEnabled['sizen'] = '4 4'
            rightEnabled['posn'] = '1 1'
            rightEnabled['style'] = 'Icons64x64_1'
            if right[2]:
                rightEnabled['substyle'] = 'Green'
            else:
                rightEnabled['substyle'] = 'LvlRed'
            if self.__editable:
                rightEnabled.setCallback(self.__setRightCallback,
                                         right[0],
                                         not right[2], 
                                         *self.__setRightCallbackArgs)
            row.append(rightEnabled)
            
            rightName = Label()
            rightName['text'] = right[0]
            rightName['sizen'] = '{:d} 4'.format(
                                    int((size[0] - buttonSize) * nameSize))
            rightName['autonewline'] = '1'
            row.append(rightName)
            
            rightDescription = Label()
            rightDescription['text'] = right[1]
            rightDescription['sizen'] = '{:d} 4'.format(
                                int((size[0] - buttonSize) * descriptionSize))
            rightDescription['autonewline'] = '1'
            row.append(rightDescription)
            rows.append(row)
        self.setTable(rows, size[0] // 10, 
                      (buttonSize, 
                        int((size[0] - buttonSize) * nameSize), 
                        int((size[0] - buttonSize) * descriptionSize)), 
                      ('Enabled', 'Right-name', 'Description'))
        
from ChatCommandButton import ChatCommandButton