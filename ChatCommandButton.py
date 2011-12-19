from WindowElements import Widget
from Manialink import *

"""
\file ChatCommandButton.py
\brief Contains the ChatCommandButten-Widget-Class
"""

class ChatCommandButton(Widget):
    """
    \brief A button to trigger a chat command
    
    When this button is pressed, its assigned chatcommand will be triggered
    """
    def __init__(self, commandLine):
        """
        \brief Construct the button
        """
        super(ChatCommandButton, self).__init__()
        self.__commandLine = commandLine #The chat command to execute
        self.__style = None #The logo on the button
        self.__image = None #The image on the button
        self.__text = None #The text of the button
        
    def setIcon(self, style):
        """
        \brief Set the icon of the button
        \param style (style, substyle) 
        """
        self.__style = style
        
    def setImage(self, image, imageFocus = None):
        """
        \brief Set the image of the button
        \param image The image url
        \param imageFocus The image url on mouseover (defaults to image)
        """
        if imageFocus != None:
            self.__image = (image, imageFocus)
        else:
            self.__image = (image, image)
        
        
    def setText(self, text):
        """
        \brief Set the text of the button
        \param text The new text
        """
        self.__text = text
        
    def getManialink(self):
        """
        \brief Get the manialink hierarchie
        """
        pos = self.getPos()
        frame = Frame()
        frame['posn'] = '{:d} {:d} {:d}'.format(*pos)
        
        bgQuad = Quad()
        bgQuad['valign'] = 'center'
        bgQuad['halign'] = 'center'
        bgQuad['style'] = 'Bgs1'
        bgQuad['substyle'] = 'BgList'
        #bgQuad['posn'] = '{:d} {:d} {:d}'.format(0, 0, 0)
        bgQuad['sizen'] = '{:d} {:d}'.format(6, 10)
        cbName = self.getWindowManager().getCallbackAddress(
                                    self.getUser(), 
                                    self.getName(), 
                                    'cb_trigger')
        bgQuad.setCallback(cbName, self.__commandLine)
        frame.addChild(bgQuad)
        
        logoQuad = Quad()
        logoQuad['halign'] = 'center'
        logoQuad['valign'] = 'center'
        logoQuad['posn'] = '{:d} {:d} {:d}'.format(0, 2, 1)
        logoQuad['sizen'] = '{:d} {:d}'.format(6, 6)
        if self.__style != None:
            logoQuad['style'] = self.__style[0]
            logoQuad['substyle'] = self.__style[1]
        
        if self.__image != None:
            logoQuad['image'] = self.__image[0]
            logoQuad['imagefocus'] = self.__image[1]
            
        logoQuad.setCallback(cbName, self.__commandLine)
        frame.addChild(logoQuad)
        
        if self.__text != None:
            textLabel = Label()
            textLabel['text'] = self.__text
            textLabel['halign'] = 'center'
            textLabel['valign'] = 'bottom'
            textLabel['posn'] = '{:d} {:d} {:d}'.format(0, -4, 1)
            textLabel['sizen'] = '{:d} {:d}'.format(5, 2)
            frame.addChild(textLabel)
        
        return frame
    
    def cb_trigger(self, entries, login, commandLine):
        """
        \brief The button was triggered, call the chat command
        \param entries Should be empty
        \param login The login of the calling player
        \param commandLine The chat command to execute
        """
        self.getWindowManager().callMethod(('TmChat', 'PlayerChat'),
                    0, 
                    login,
                    commandLine,
                    True)