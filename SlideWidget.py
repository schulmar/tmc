from WindowElements import *
from ChatCommandButton import *
from os import linesep

"""
\file SlideWidget.py
\brief Contains the SlideWidget plugin
"""

class SlideWidget(Widget):
    """
    \class SlideWidget
    \brief The SlideWidgetPlugin
    
    This plugin holds severall ChatCommandButtons and displays them on demand
    """
    def __init__(self):
        """
        \brief Construct the widget
        \param pipes The communication pipes to the PluginManager
        \param args Additional startup arguments
        """
        super(SlideWidget, self).__init__()
        self.__commandButtons = []
        
    def initialize(self, buttonList):
        """
        \brief Initialize the widget
        \param buttonList A list of dictionaries that define buttons
        """
        if isinstance(buttonList, list):
            for i in buttonList:
                try:
                    commandLine = i['command']
                except KeyError:
                    commandLine = None
                    
                newButton = ChatCommandButton(commandLine)
                
                try:
                    newButton.setIcon(i['icon'])
                except KeyError:
                    pass
                
                try:
                    newButton.setText(i['text'])
                except KeyError:
                    pass
                
                try:
                    newButton.setImage(i['image'], i.get('imagefocus', i['image']))
                except KeyError:
                    pass
                
                try:
                    newButton.setManialink(i['manialink'])
                except KeyError:
                    pass
                
                self.__commandButtons.append(newButton)
            
    def setUser(self, name):
        """
        \brief Set the user of this window
        """
        super(SlideWidget, self).setUser(name)
        for b in self.__commandButtons:
            b.setUser(name)
            
    def addButton(self, button):
        """
        \brief Add a new button to the SlideWidget
        \param button The new button
        """
        button.setName(str(len(self.__commandButtons)))
        self.__commandButtons.append(button)    
         
    def getCallbackAddress(self, login, windowName, functionName):
        """
        \brief Get the callback address for the window
        \param login The login of the user to display to
        """
        return self.getWindowManager().getCallbackAddress(login, 
                                          self.getName(), 
                                          windowName + '.' + functionName)
        
    def callMethod(self, *args):
        self.getWindowManager().callMethod(*args)
        
    def callFunction(self, *args):
        return self.getWindowManager().callFunction(*args)
    
    def signalEvent(self, *args):
        self.getWindowManager().signalEvent(*args)
    
    def __getattr__(self, name):
        """
        \brief Get the target of the calls from other plugins
        \param name The name of the target
        """
        if not '.' in name:
                return getattr(super(SlideWidget, self), name)
        try:
            splitList = name.split('.')
            return getattr(self.__commandButtons[int(splitList[0])], '.'.join(splitList[1:]))
        except TypeError:
            raise AttributeError
        except KeyError:
            print('Trying to access non existing button ', splitList[0])
            raise
           
        
    def getManialink(self):
        """
        \brief Return the manialink hierarchie of this widget
        """
        size = self.getSize()
        mainFrame = Frame()
        mainFrame['id'] = 'mainFrame'
        
        mainFrame['posn'] = '60 10 1'
        
        contentFrame = Frame()
        contentFrame['posn'] = '{:d} {:d} 1'.format(1, size[1] // 2 - 1)
        
        x = 0
        y = 0
        
        for c in self.__commandButtons:
            c.setWindowManager(self)
            buttonSize = c.getSize()
            #buttonFrame = Frame()
            buttonFrame = c.getManialink()
            buttonFrame['posn'] = '{:d} {:d} 1'.format(x + buttonSize[0], 
                                                     y - buttonSize[1] // 2)
            
            y -= buttonSize[1]
            if -y > size[1] + buttonSize[1]:
                y = 0
                x += buttonSize[0] 
            
            #ml = c.getManialink()
            #buttonFrame.addChild(ml)
            #print(ml.getXML())
            
            contentFrame.addChild(buttonFrame)
        if x != 0:
            size = (x + 10, size[1])
        else:
            size = (x + 10, y + 10)
            
        mainFrame.addChild(contentFrame)
        
        bgQuad = Quad()
        bgQuad['sizen'] = '{:d} {:d}'.format(size[0], size[1] + 5)
        bgQuad['posn'] = '{:d} {:d} {:d}'.format(2, size[1] // 2, 0)
        bgQuad['style'] = 'Bgs1InRace'
        bgQuad['substyle'] = 'BgCardList'
        bgQuad['ScriptEvents'] = '1'
        mainFrame.addChild(bgQuad)
        
        ms = ManiaScript()
        variables = [{'name' : 'Integer windowWidth', 'value' : str(int(size[0] * 160 / 64))}
                     ]
        ms.setContent(self.getManiaScript(variables))
        mainFrame.addChild(ms)
        
        return mainFrame
    
    def getManiaScript(self, variables):
        """
        \brief Return the maniascript code with global variables
        """
        globalVariables = ''
        for v in variables:
            globalVariables += ('declare ' + v['name'] 
                            + ' = ' + v['value'] 
                            + ';' + linesep)
        return '''

main() 
{ 
    ''' +  globalVariables + '''

    declare Boolean moveOut;
    declare CGameManialinkFrame mainFrame <=> (Page.MainFrame.Controls["mainFrame"] as CGameManialinkFrame); 
    while(True)
    {
        foreach(Event in PendingEvents)
        {
            switch(Event.Type)
            {
                case CGameManialinkScriptEvent::Type::MouseClick:
                { 
                    moveOut = !moveOut;                    
                }
                default: 
                {
                    //log(Event.Type);
                    //log(Event.ControlId);
                }
            }
        }
        if(moveOut)
        {
            if(mainFrame.PosnX > 160 - windowWidth)
                    mainFrame.PosnX -= 1;
        }
        else
        {
            if(mainFrame.PosnX < 150)
                mainFrame.PosnX += 1;
        }
        yield;
        //sleep(20);
    }
}
'''