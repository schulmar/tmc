from PluginInterface import *
from Manialink import *

class Test(PluginInterface):
	def __init__(self, pipes, args):
		super(Test, self).__init__(pipes)

	def initialize(self, args):
		self.callMethod(('TmChat', 'registerChatCommand'), 'mltest', ('Test', 'chat_mltest'))
		self.callMethod(('TmChat', 'registerChatCommand'), 'wdtest', ('Test', 'chat_wdtest'))
		self.callMethod(('TmChat', 'registerChatCommand'), 'oltest', ('Test', 'chat_oltest'))

	def chat_mltest(self, login, args):
		ml = Frame()
		lbl = Label()
		lbl['text'] = 'Text:'
		lbl['posn'] = '0 0'
		lbl['sizen'] = '10 2'
		ml.addChild(lbl)
		q = Quad()
		q['sizen'] = '10 2'
		q['bgcolor'] = '0009'
		q['manialink'] = 'POST(http://sektor.selfip.com:8888/manialink/fileentry.php?file=fileEntry,fileEntry)'
		q.setCallback(('Test', 'ManialinkAnswer'))
		ml.addChild(q)
		e = FileEntry()
		e['name'] = 'fileEntry'
		e['posn'] = '5 0'
		e['sizen'] = '10 2'
		e['folder'] = ''
		ml.addChild(e)
		self.callMethod(('ManialinkManager', 'displayManialinkToLogin'), ml, 'Test.test', login)

	def chat_wdtest(self, login, args):
		content = []
		for i in xrange(100):
			lbl1 = Label()
			lbl1['text'] = 'Row ' + str(i)
			lbl2 = Label()
			lbl2['text'] = 'Column 2'
			content.append([lbl1, lbl2])
		self.callMethod(('WindowManager', 'displayTableWindow'), login, 'Test.wdtest', 'Test', (80,80), (-40,40,0), content, 10, (10, 20))

	def chat_oltest(self, login, args):
		ml = Frame()
		ml.setContent(
		"""<quad bgcolor="FFF9" sizen="5 5"/>
		<format halign="center" />
		<quad bgcolor="0009" sizen="5 5" />""")
		self.callMethod(('ManialinkManager', 'displayManialinkToLogin'), ml, 'Test.old', login)
