from PluginInterface import *
from multiprocessing import Process, Pipe
import threading
import os
import traceback

"""
\file PluginManager.py
\brief Contains the PluginManager class
"""

class PluginManager(object):
	"""
	\brief This class is the central communicator between all plugins
	
	Each plugin is registered here and will be started from here!
	"""
	def __init__(self):
		"""
		\brief Initialize with no plugins
		"""
		self.plugins = {} #The map from plugin names to plugin contents

	def loadPlugin(self, caller, fileName, args = None):
		"""
		\brief Load the plugin in the file 
		\param caller The name of the plugin that requests this load 
		\param fileName The filename of the plugin to load
		\param args Startup arguments to this plugin
		"""
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
		"""
		\brief Start the plugin process
		\param name The name of the plugin to start
		\param args The startup arguments of this plugin
		"""
		plugin = self.plugins[name]
		plugin.running = True
		plugin.threads[0].start()
		plugin.threads[1].start()
		plugin.process.start()
		plugin.pipes[0].send(True)
		plugin.pipes[0].send(Method('initialize', (args,)))
		print('Started plugin ' + name)

	def __StopPlugin(self, name):
		"""
		\brief Stop the named plugin
		\param name The name of the plugin to stop
		"""
		try:
			plugin = self.plugins[name]
		except KeyError:
			print('Could not stop unknown plugin ' + str(name))
			return False
		plugin.req_lock.acquire()
		plugin.pipes[0].send(Stop())
		plugin.req_lock.release()

		plugin.running = False
		plugin.process.join()

	def unloadPlugin(self, name):
		"""
		\brief Unload a plugin from the manager
		\param name The name of the plugin to unload
		
		This first stops the plugin and then removes it from the plugin list
		"""
		
		self.__StopPlugin(name)
		try:
			plugin = self.plugins[name]
		except KeyError:
			return False
		for p in self.plugins.items():
			for l in p[1].listeners.items():
				p[1].listeners[l[0]] = (l[1], filter(lambda x: plugin != x[0],l[1]))
		del self.plugins[name]
		print('Unloaded plugin list: ', self.plugins)

	def restartPlugin(self, caller, name):
		"""
		\brief Restart the plugin
		\param caller The one demanding the restart
		\param name THe name of the plugin to restart
		"""
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
		"""
		\brief Shutdown the whole system
		
		Shuts down all plugins and then the manager
		"""
		for plugin in self.plugins.keys():
			self.__StopPlugin(plugin)
		del self.plugins

	def PluginList(self, caller):
		"""
		\brief Get the list of all plugin names
		\param caller The name of the calling plugin
		"""
		return self.plugins.keys()

	def __listenForRequests(self, pluginName):
		"""
		\brief The listener function for incoming requests
		\param pluginName The plugin to listen for
		
		This function listens for outgoing requests from the named plugin,
		each in its own thread to not block the others
		"""
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
						try:
							method = getattr(self, request.name[1])
						except:
							print('Could not call method PluginManager.' + 
								str(request.name[1]) + str(request.getArgs()))
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
						try:
							function = getattr(self, request.name[1])
						except:
							print('Could not call function PluginManager.' + 
								str(request.name[1]) + str(request.getArgs()))
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
		"""
		\brief This function listens for answers from the plugin
		\param pluginName The plugin to listen on
		
		Each plugin has an affiliated thread that runs this function
		and listens for answers on requests that were made to this plugin
		"""
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
		"""
		\brief Subscribe a plugin function to an event of a plugin
		\param caller The subscriber
		\param pluginName The plugin that gets subscribed
		\param eventName The event of the plugin that gets subscribed
		\param callbackMethod The name of the callbackMethod to the event
		"""
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
		"""
		\brief Unsubscribe from an event
		\param caller The plugin that unsubscribes
		\param pluginName The plugin from which to unsubscribe
		\param eventName The event from which to unsubscribe
		\param callbackMethod The callbackMethod to unsubsribe
		"""
		plugin = self.plugins[pluginName]
		item = (caller, callbackMethod)
		if item in plugin.listeners[eventName]:
			plugin.listeners[eventName].remove(item)


class PluginElement:
	"""
	\brief A placeholder class to manage a plugin in the pluginManager
	"""
	def __init__(self, name, depends, provides, pipes, threads, process, fileName, args):
		self.depends = depends #The dependencies of this plugin
		self.provides = provides #The provided functionality of this plugin
		self.name = name #The name of this plugin
		self.running = False #The running state of this plugin
		self.threads = threads #The threads of this plugin
		self.process = process #The process instance of this plugin
		self.req_lock = threading.Lock() #The request lock of this plugin
		self.pipes = pipes #The communication pipes oft his plugin
		self.listeners = {} #The event listeners to this plugin
		self.fileName = fileName #The fileName of the plugin file
		self.args = args #The initial args of this plugin

