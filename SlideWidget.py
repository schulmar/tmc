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
            
    def addButton(self, button):
        """
        \brief Add a new button to the SlideWidget
        \param button The new button
        """
        self.__commandButtons.append(button)
         
    def getManialink(self):
        """
        \brief Return the manialink hierarchie of this widget
        """
        size = self.getSize()
        mainFrame = Frame()
        mainFrame['id'] = 'mainFrame'
        
        mainFrame['posn'] = '60 0 1'
        
        bgQuad = Quad()
        bgQuad['sizen'] = '{:d} {:d}'.format(size[0] + 2, size[1])
        bgQuad['posn'] = '{:d} {:d} {:d}'.format(2, size[1] // 2, 0)
        mainFrame.addChild(bgQuad)
        
        ms = ManiaScript()
        variables = [{'name' : 'Integer windowWidth', 'value' : str(size[0])}
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

    declare Boolean mouseWasOver;
    declare CGameManialinkControl mainFrame <=> Page.MainFrame.Controls["mainFrame"]; 
    while(True)
    {
        mouseWasOver = False;
        foreach(Event in PendingEvents)
        {
            switch(Event.Type)
            {
                case CGameManialinkScriptEvent::Type::MouseOver:
                {
                    if(Event.ControlId == "mainFrame")
                    {
                        if(mainFrame.PosnX > 64 - windowWidth)
                            mainFrame.PosnX -= 1; 
                        mouseWasOver = True;
                    }                    
                }
            }
        }
        if(!mouseWasOver)
        {
            if(mainFrame.PosnX < 62)
                mainFrame.PosnX += 1;
        }
        yield;
        sleep(20);
    }
}
'''