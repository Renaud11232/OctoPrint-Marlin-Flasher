from subprocess import Popen, PIPE
from threading import Thread


class RemoteAgentStatus:

	STARTING = "starting"
	RUNNING = "running"
	STOPPING = "stopping"
	STOPPED = "stopped"
	FLASHING = "flashing"

	def __init__(self):
		raise Exception("This class is an enum like, the constructor should not be called")


class PlatformIoRemoteAgent:

	def __init__(self, configuration, logger, printer):
		self.__status_observers = []
		self.__log_observers = []
		self.__status = RemoteAgentStatus.STOPPED
		self.__process = None
		self.__config = configuration
		self.__logger = logger
		self.__stdout_thread = None
		self.__stderr_thread = None
		self.__printer = printer

	def add_status_observer(self, callback):
		self.__status_observers.append(callback)

	def __notify_status_change(self):
		self.__logger.info("PlatformIO remote agent is %s" % self.__status)
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
		if self.__process is None:
			self.__status = RemoteAgentStatus.STARTING
			self.__notify_status_change()
			command = [self.__config.get_platformio_cli_path(), "remote", "agent", "start"]
			self.__logger.debug("Running %s" % " ".join(command))
			p = Popen(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
			self.__process = p
			self.__stdout_thread = Thread(target=self.__handle_log, args=(p.stdout,), daemon=True)
			self.__stderr_thread = Thread(target=self.__handle_log, args=(p.stderr,), daemon=True)
			self.__stdout_thread.start()
			self.__stderr_thread.start()
			Thread(target=self.__process_handler, daemon=True).start()
			return True
		else:
			self.__logger.debug("There's another process already running, not starting a new agent")
			return False

	def stop(self):
		if self.__process is not None:
			self.__status = RemoteAgentStatus.STOPPING
			self.__notify_status_change()
			self.__process.terminate()
			return True
		else:
			self.__logger.debug("There's no process running, not stopping the agent as it's not started")
			return False

	def __handle_log(self, stream):
		for line in stream:
			line = line.rstrip()
			self.__notify_log(line)
			self.__logger.debug(line)
			if self.__status == RemoteAgentStatus.STARTING and "successfully authorized" in line.lower():
				self.__status = RemoteAgentStatus.RUNNING
				self.__notify_status_change()
			elif self.__status == RemoteAgentStatus.RUNNING and "remote command received : run" in line.lower():
				self.__status = RemoteAgentStatus.FLASHING
				self.__notify_status_change()
				# TODO disconnect printer
			elif self.__status == RemoteAgentStatus.FLASHING and "somestring" in line.lower():
				self.__status = RemoteAgentStatus.RUNNING
				self.__notify_status_change()
				# TODO reconnect printer

	def __process_handler(self):
		self.__logger.debug("Waiting for the agent to stop...")
		self.__stdout_thread.join()
		self.__stderr_thread.join()
		self.__process.wait()
		self.__logger.debug("Process exited with status : %d" % self.__process.returncode)
		self.__process = None
		self.__status = RemoteAgentStatus.STOPPED
		self.__notify_status_change()
