class RemoteAgentStatus:

	STARTING = "starting"
	RUNNING = "running"
	STOPPING = "stopping"
	STOPPED = "stopped"

	def __init__(self):
		raise Exception("This class is an enum like, the constructor should not be called")


class PlatformIoRemoteAgent:

	def __init__(self, configuration):
		self.__status_observers = []
		self.__log_observers = []
		self.__status = RemoteAgentStatus.STOPPED
		self.__process = None
		self.__config = configuration

	def add_status_observer(self, callback):
		self.__status_observers.append(callback)

	def __notify_status_change(self):
		for observer in self.__status_observers:
			observer()

	def add_log_observer(self, callback):
		self.__log_observers.append(callback)

	def __notify_log(self, line):
		for observer in self.__log_observers:
			observer(line)

	def get_status(self):
		return self.__status

	def start(self):
		self.__status = RemoteAgentStatus.STARTING
		self.__notify_status_change()

	def stop(self):
		self.__status = RemoteAgentStatus.STOPPING
		self.__notify_status_change()
