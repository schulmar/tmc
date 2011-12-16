import imp,threading,os,cPickle

def loadPlugin(fileName, pipes, args):
	pluginPath,name = os.path.split(fileName)
	className = os.path.splitext(name)[0]
	os.chdir(pluginPath)
	pluginModule = __import__(className)	
	pluginClass = getattr(pluginModule, className)
	if pipes[0].recv():
		pluginInstance = pluginClass(pipes, args)
		pluginInstance.run()


class PluginInterface(object):
	def __init__(self, pipes):
		self.inPipe = pipes[0]
		self.outPipe = pipes[1]
		self.queue = []
		self.hasWork = threading.Condition()
		self.workerThread = threading.Thread(target=self.__work)
		self.__running = False
		self.__questioner = None
	
	def initialize(self, args):
		pass

	@staticmethod
	def getDependencies(args):
		return []

	@staticmethod
	def getFunctions(args):
		return []

	def run(self):
		self.__running = True
		self.workerThread.deamon = True
		self.workerThread.start()
		while self.__running:
			try:
				task = self.inPipe.recv()
				self.hasWork.acquire()
				self.queue.append(task)
				self.hasWork.notify()
				self.hasWork.release()
			except KeyboardInterrupt:
				self.__stop()
			except Exception as e:
				print(self, e)
			
	def shutDown(self):
		pass

	def __stop(self):
		self.__running = False
		self.outPipe.send(Stop())
		self.shutDown()
	
	def __outPipeSend(self, content):
		self.outPipe.send(content)

	def signalEvent(self, eventName, *args):
		self.__outPipeSend(Event(eventName, args))

	def callMethod(self, name, *args):
		self.__outPipeSend(Method(name, args))

	def callFunction(self, name, *args):
		#Clear any previous answers if there are some
		while self.outPipe.poll():
			self.outPipe.recv()

		self.__outPipeSend(Function(name, args))

		result = self.outPipe.recv()
		return result.getValue()
	
	def log(self, *args):
		string = ''
		for i in args:
			string += ' ' + str(i)
		self.callMethod(('Logger', 'log'), self.__class__.__name__ + ': ' + string)

	def questioner(self):
		return self.__questioner

	def __work(self):
		while self.__running:
			try:
				self.hasWork.acquire()
				while len(self.queue) < 1:
					self.hasWork.wait()
				job = self.queue[0]
				del self.queue[0]
				self.hasWork.release()
				
				if isinstance(job, Stop):
					self.__running = False
				elif isinstance(job, Method):
					try:
						method = getattr(self, job.name)
					except AttributeError:
						print('Unknown method ' + self.__class__.__name__ + '.'
							 + job.name + str(job.getArgs()))
					self.__questioner = str(job.questioner)
					try:
						method(*job.getArgs())
					except TypeError:
						print('Used wrong arguments in method call ' 
							+ self.__class__.__name__ + '.' + job.name + str(job.getArgs()) 
							+ ' from ' + str(job.questioner))
						raise
					except:
						print('Exception in method call ' 
							+ self.__class__.__name__ + '.' + job.name + str(job.getArgs()) 
							+ ' from ' + str(job.questioner))
						raise
				elif isinstance(job, Event):
					pass
				elif isinstance(job, Function):
					try:
						function = getattr(self, job.name)
					except AttributeError:
						print('Unknown function ' + self.__class__.__name__ + '.'
							+ job.name + str(job.getArgs()))
					self.__questioner = job.questioner
					try:
						value = function(*job.getArgs())
					except TypeError:
						print('Used wrong arguments in function call ' 
							+ self.__class__.__name__ + '.' + job.name + str(job.getArgs())
							+ ' from ' + job.questioner)
						raise
					except:
						print('Exception in function call ' 
							+ self.__class__.__name__ + '.' + job.name + str(job.getArgs()) 
							+ ' from ' + job.questioner)
						raise
					self.inPipe.send(Result(job, value))
			except KeyboardInterrupt:
				self.__stop()
				

				

class Function:
	def __init__(self, name, args, questioner = None):
		self.name = name
		self.args = cPickle.dumps(args)
		self.questioner = questioner

	def getArgs(self):
		return cPickle.loads(self.args)

class Method(Function):
	pass

class Event(Function):
	pass

class Result:
	def __init__(self, function, result):
		self.function = function
		self.value = cPickle.dumps(result)

	def getValue(self):
		return cPickle.loads(self.value)

class Stop:
	pass

class Error(Exception):
	pass
