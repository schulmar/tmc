from PluginInterface import *
from multiprocessing import Process, Pipe
import threading
import os
import traceback

class PluginManager(object):
	def __init__(self):
		self.plugins = {}

	def loadPlugin(self, caller, fileName, args = None):
		pipe0, childPipe0 = Pipe()
		pipe1, childPipe1 = Pipe()
		p = Process(target = loadPlugin, args = (fileName, (childPipe0, childPipe1), args))
		pluginName = os.path.splitext(os.path.split(fileName)[1])[0]
		t1 = threading.Thread(target = self.__listenForRequests, args = (pluginName,))
		t1.deamon = True
		t2 = threading.Thread(target = self.__listenForAnswers, args = (pluginName,))
		t2.deamon = True
		self.plugins[pluginName] = PluginElement(pluginName, [], [], (pipe0, pipe1), (t1, t2), p, fileName, args)
		self.__StartPlugin(pluginName, args)

	def __StartPlugin(self, name, args = None):
		plugin = self.plugins[name]
		plugin.running = True
		plugin.threads[0].start()
		plugin.threads[1].start()
		plugin.process.start()
		plugin.pipes[0].send(True)
		plugin.pipes[0].send(Method('initialize', (args,)))
		print('Started plugin ' + name)

	def __StopPlugin(self, name):
		plugin = self.plugins[name]

		plugin.req_lock.acquire()
		plugin.pipes[0].send(Stop())
		plugin.req_lock.release()

		plugin.running = False
		plugin.process.join()

	def unloadPlugin(self, name):
		self.__StopPlugin(name)
		plugin = self.plugins[name]
		for p in self.plugins.items():
			for l in p[1].listeners.items():
				p[1].listeners[l[0]] = (l[1], filter(lambda x: plugin != x[0],l[1]))
		del self.plugins[name]
		print('Unloaded plugin list: ', self.plugins)

	def restartPlugin(self, caller, name):
		if name in self.plugins:
			print('Restarting plugin ' + str(name) + ' on request of ' + str(caller.name))

			plugin = self.plugins[name]
			args = plugin.args
			fileName = plugin.fileName

			self.unloadPlugin(name)
			self.loadPlugin(caller, fileName, args)
		else:
			print('Plugin ' + str(name) + ' not found in list for restart')


	def shutdown(self):
		for plugin in self.plugins.keys():
			self.__StopPlugin(plugin)
		del self.plugins

	def PluginList(self, caller):
		return self.plugins.keys()

	def __listenForRequests(self, pluginName):
		try:
			plugin = self.plugins[pluginName]
			while plugin.running:
				request = plugin.pipes[1].recv()

				if isinstance(request, Event):
					#print('Processing Event ' + str(request.name))
					if request.name in plugin.listeners:
						for listener in plugin.listeners[request.name]:
							listener[0].req_lock.acquire()
							method = Method(listener[1], None)
							method.args = request.args
							method.questioner = plugin.name
							listener[0].pipes[0].send(method)
							listener[0].req_lock.release()

				elif isinstance(request, Method):
					if request.name[0] == None:
						#print('Processing Method ' + str(request.name[1] + str(request.getArgs())))
						method = getattr(self, request.name[1])
						method(plugin, *request.getArgs())
					else:
						try:
							recipient = self.plugins[request.name[0]]
							recipient.req_lock.acquire()
							request.name = request.name[1]
							request.questioner = plugin.name
							recipient.pipes[0].send(request)
							recipient.req_lock.release()
						except KeyError:
							print('Could not pass method request to ' + request.name[0] + '.' + request.name[1])

				elif isinstance(request, Function):
					if request.name[0] == None:
						#print('Processing Function ' + str(request.name[1]) + str(request.getArgs()))
						function = getattr(self, request.name[1])
						plugin.pipes[1].send(Result(request, function(plugin, *request.getArgs())))
					elif request.name[0] in self.plugins:
						recipient = self.plugins[request.name[0]]
						recipient.req_lock.acquire()
						request.name = request.name[1]
						request.questioner = plugin.name
						recipient.pipes[0].send(request)
						recipient.req_lock.release()
					else:
						plugin.pipes[1].send(Error())
				elif isinstance(request, Stop):
					plugin.running = False
				else:
					print('Could not process ' + str(request))
		except KeyboardInterrupt:
			print('Interrupted')
			self.__StopPlugin(pluginName)
	#	except Exception as e:
	#		print(self, pluginName, e, plugin)
		finally:
			pass

	def __listenForAnswers(self, pluginName):
		try:
			plugin = self.plugins[pluginName]
			while plugin.running:
				answer = plugin.pipes[0].recv()

				if isinstance(answer, Stop):
					plugin.running = False
				else:
					q = answer.function.questioner
					if q in self.plugins:
						q = self.plugins[q]
						q.pipes[1].send(answer)
		except KeyboardInterrupt:
			self.__StopPlugin(pluginName)
		except Exception as e:
			print(self, pluginName, e)
		finally:
			pass

	def subscribeEvent(self, caller, pluginName, eventName, callbackMethod):
		try:
			plugin = self.plugins[pluginName]
			if not eventName in plugin.listeners:
				plugin.listeners[eventName] = []
			plugin.listeners[eventName].append((caller, callbackMethod))
			return True
		except Exception as e:
			print('Error while subscribing to', pluginName, eventName, callbackMethod)
			raise e
			return False

	def unsubscribeEvent(self, caller, pluginName, eventName, callbackMethod):
		plugin = self.plugins[pluginName]
		item = (caller, callbackMethod)
		if item in plugin.listeners[eventName]:
			plugin.listeners[eventName].remove(item)


class PluginElement:
	def __init__(self, name, depends, provides, pipes, threads, process, fileName, args):
		self.depends = depends
		self.provides = provides
		self.name = name
		self.running = False
		self.threads = threads
		self.process = process
		self.req_lock = threading.Lock()
		self.pipes = pipes
		self.listeners = {}
		self.fileName = fileName
		self.args = args

