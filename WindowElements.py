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
            
    def getManialink(self):
        pass
            
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
        submitButtonBgQuad.setCallback(self.__callback)
        mainFrame.addChild(submitButtonBgQuad)
        
        submitButtonLabel = Label()
        submitButtonLabel['halign'] = 'right'
        submitButtonLabel['posn'] = '{:d} {:d} 2'.format(size[0] - 6, 7 - size[1])
        submitButtonLabel['sizen'] = '8 3'
        submitButtonLabel['text'] = 'Submit'
        submitButtonLabel.setCallback(self.__callback)
        mainFrame.addChild(submitButtonLabel)

        return mainFrame

class Window(Widget):
    """
    \brief The basic window class
    """
    
    def __init__(self, title):
        super(Window, self).__init__()
        self.__closeButton = True #Should this window have a close button?
        self.__title = 'Default Title' #The title of the window
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
        
class CommentOutput(PagedWindow):
    """
    \brief Prints some comments on the screen
    """
    def __init__(self, title, comments):
        """
        \brief Create a paged window with the comments
        \param title The title of the window
        \param comments The comments as given by Karma.getComments
        """
        pages = map(self.__getCommentMl, comments)
        super(CommentOutput, self).__init__(title, pages)
        
        self.__commentVoteCallback = (None, None) #The callback on comment votes
        self.__commentEditCallback = (None, None) #The callback for editing comments
        self.__commentDeleteCallback = (None, None) #The callback for deleting comments
        
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
    
    def __getCommentMl(self, comment):
        """
        \brief Setup the Manialink for one comment
        \param comment Expected {depth, height, karma, votable, editable, deletable, answerable, nickName, commentTuple}
        \return The manialink
        """
        indent = 2 * comment['depth']
        width = self.getSize()[0] - indent 
        height = comment['height']
        
        commentFrame = Frame()
        commentFrame['posn'] = '{:d} {:d}'.format(indent, 0)
        
        commentBgQuad = Quad()
        commentBgQuad['sizen'] = '{:d} {:d}'.format(width, height + 10)
        commentBgQuad['style'] = 'Bgs1'
        commentBgQuad['substyle'] = 'BgWindow1'
        commentFrame.addChild(commentBgQuad)
        
        headBarBgQuad = Quad()
        headBarBgQuad['sizen'] = '{:d} {:d}'.format(width - 2, 3)
        headBarBgQuad['posn'] = '1 -1 1'
        headBarBgQuad['style'] = 'Bgs1'
        headBarBgQuad['substyle'] = 'BgTitle3'
        commentFrame.addChild(headBarBgQuad)
        
        nameLabel = Label()
        nameLabel['text'] = comment['nickName']
        nameLabel['posn'] = '2 -2 2'
        nameLabel['sizen'] = '{:d} {:d}'.format(width // 2 - 2, 2)
        commentFrame.addChild(nameLabel)
        
        votesFrame = Frame()
        votesFrame['posn'] = '{:d} {:d} 1'.format(width // 2, -1)
        commentFrame.addChild(votesFrame)
        
        voteDown = Quad()
        voteDown['posn'] = '0 0 1'
        voteDown['sizen'] = '2 2'
        voteDown['style'] = 'Icons64x64_1'
        voteDown['substyle'] = 'ArrowDown'
        voteDown.setCallback(self.__commentVoteCallback, comment['commentTuple'][0], 0)
        votesFrame.addChild(voteDown)
        
        karmaLabel = Label()
        karmaLabel['text'] = '{:d}%'.format(comment['commentTuple'][1])
        karmaLabel['posn'] = '{:d} {:d} 1'.format(4, 0)
        karmaLabel['sizen'] = '4 2'
        votesFrame.addChild(karmaLabel)
        
        voteUp = Quad()
        voteUp['posn'] = '10 0 1'
        voteUp['sizen'] = '2 2'
        voteUp['style'] = 'Icons64x64_1'
        voteUp['substyle'] = 'ArrowUp'
        voteUp.setCallback(self.__commentVoteCallback, comment['commentTuple'][0], 100)
        votesFrame.addChild(voteUp)
        
        footBarBgQuad = Quad()
        footBarBgQuad['sizen'] = '{:d} {:d}'.format(width - 2, 3)
        footBarBgQuad['valing'] = 'bottom'
        footBarBgQuad['posn'] = '{:d} {:d} 1'.format(1, 1 - (height + 10))
        footBarBgQuad['style'] = 'Bgs1'
        footBarBgQuad['style'] = 'BgTitle2'
        commentFrame.addChild(footBarBgQuad)
        
        return commentFrame