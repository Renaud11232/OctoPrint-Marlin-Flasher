import json
import sys
from .base_flasher import BaseFlasher
from collections import deque
from subprocess import Popen, PIPE
import zipfile
import os
import shutil
import re
from threading import Thread
from datetime import datetime
import serial
import flask
import platform
from flask_babel import gettext
from .platformio_remote import PlatformIoRemoteAgent


class PlatformIOFlasher(BaseFlasher):

	def __init__(self, settings, printer, plugin, plugin_manager, identifier, logger):
		BaseFlasher.__init__(self, settings, printer, plugin, plugin_manager, identifier, logger)
		self.__remote_agent = PlatformIoRemoteAgent(settings)
		self.__remote_agent.add_status_observer(self.__push_remote_agent_status)
		self.__remote_agent.add_log_observer(self.__push_remote_agent_log)

	def start_install(self):
		system = platform.system()
		self._logger.debug("platform.system() = %s" % system)
		if system == "Windows":
			exec_folder = "Scripts"
		else:
			exec_folder = "bin"
		self._background_run(self.__install, args=(exec_folder, system))
		return dict(
			message=gettext("The installation of platformio-core is started")
		), None

	def __install(self, exec_folder, system):
		venv_path = os.path.join(self._plugin.get_plugin_data_folder(), "platformio")
		if os.path.exists(venv_path):
			self._logger.info("Previous installation found in %s, removing it" % venv_path)
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="platformio_install",
				finished=False,
				status=gettext("Previous installation found in %s, removing it") % venv_path
			))
			shutil.rmtree(venv_path)

		def handle_log(stream):
			for line in stream:
				line = line.rstrip()
				self._logger.info(line)
				self._plugin_manager.send_plugin_message(self._identifier, dict(
					type="platformio_install",
					finished=False,
					status=line
				))
		if system == "Windows":
			exec_ext = ".exe"
		else:
			exec_ext = ""
		new_exec_path = os.path.join(venv_path, exec_folder, "python" + exec_ext)
		success = self.__exec([sys.executable, "-m", "virtualenv", "-p", "python3", venv_path], handle_log, handle_log) \
			and self.__exec([new_exec_path, "-m", "pip", "install", "platformio", "--no-cache-dir"], handle_log, handle_log)
		if success:
			pio_path = os.path.join(venv_path, exec_folder, "pio" + exec_ext)
			self._logger.info("Platformio installed successfully in %s" % pio_path)
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="platformio_install",
				finished=True,
				success=True,
				status=gettext("Successfully installed Platformio in %s") % venv_path,
				path=pio_path
			))
		else:
			self._logger.warning("Failed to install platformio")
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="platformio_install",
				finished=True,
				success=False,
				status=gettext("The installation failed")
			))

	def __exec(self, command, stdout_handler, stderr_handler, show_in_logs=True):
		if show_in_logs:
			self._logger.debug("Executing command : %s" % " ".join(command))
		with Popen(command, stdout=PIPE, stderr=PIPE, universal_newlines=True) as p:
			stdout_thread = Thread(target=stdout_handler, args=(p.stdout,))
			stderr_thread = Thread(target=stderr_handler, args=(p.stderr,))
			stdout_thread.start()
			stderr_thread.start()
			p.wait()
			self._logger.debug("The command exited with status %d" % p.returncode)
			return p.returncode == 0

	def _validate_firmware_file(self, file_path):
		self._logger.debug("Validating firmware file...")
		try:
			with zipfile.ZipFile(file_path, "r") as _:
				return None
		except zipfile.BadZipfile:
			self._logger.debug("The firmware file does not have a valid file type")
			return [gettext("Invalid file type.")]

	def _handle_firmware_file(self, firmware_file_path):
		self._firmware = None
		self._firmware_version = None
		self._firmware_author = None
		self._firmware_upload_time = None
		with zipfile.ZipFile(firmware_file_path, "r") as zip_file:
			firmware_dir = os.path.join(self._plugin.get_plugin_data_folder(), "firmware_platformio")
			if os.path.exists(firmware_dir):
				shutil.rmtree(firmware_dir)
			os.makedirs(firmware_dir)
			self._logger.debug("Extracting firmware archive...")
			zip_file.extractall(firmware_dir)
			self._logger.debug("Browsing files...")
			for root, dirs, files in os.walk(firmware_dir):
				for f in files:
					if f == "platformio.ini":
						self._logger.debug("Found platformio.ini")
						self._firmware = root
						self._firmware_upload_time = datetime.now()
			if self._firmware:
				self._find_firmware_info()
				return dict(
					path=self._firmware,
					file="platformio.ini"
				), None
			return None, [gettext("No PlatformIO configuration file were found in the given file.")]

	def check_setup_errors(self):
		self._logger.debug("Checking PlatformIO configuration...")
		no_platformio_path = self._settings.get_platformio_cli_path() is None
		if no_platformio_path:
			self._logger.info("No PlatformIO path was configured")
			return [gettext("No path has been configured, check the plugin settings.")]
		version_logs = deque()

		def handle_logs(stream):
			for line in stream:
				self._logger.debug(line.rstrip())
				version_logs.append(line)

		success = self.__exec([self._settings.get_platformio_cli_path(), "--version"], handle_logs, handle_logs)
		version_logs = "".join(version_logs)
		if not success or "platformio" not in version_logs.lower():
			self._logger.info("The configured path does not point to PlatformIO-Core")
			return [gettext("The configured path does not point to PlatformIO-Core.")]
		return []

	def flash(self):
		if self._firmware is None:
			self._logger.debug("No firmware uploaded")
			return None, [gettext("You did not upload the firmware or it got reset by the previous flash process.")]
		if not self._printer.is_ready():
			self._logger.debug("Printer not ready")
			return None, [gettext("The printer may not be connected or it may be busy.")]
		env = None
		if "env" in flask.request.values and flask.request.values["env"]:
			env = flask.request.values["env"]
		thread = Thread(target=self.__background_flash, args=(env,))
		thread.start()
		self._logger.debug("Saving options")
		self._settings.set_platformio_last_flash_options(flask.request.values.to_dict())
		self._settings.save()
		self.__push_last_flash_option()
		return dict(
			message=gettext("Flash process started.")
		), None

	def __background_flash(self, env):
		self._logger.info("Starting flashing process...")
		self._flash_status = dict(
			step_name=gettext("Compiling"),
			progress=0,
			finished=False
		)
		self._push_flash_status("platformio_flash_status")
		pio_args = [self._settings.get_platformio_cli_path(), "run", "-d", self._firmware]
		if env:
			pio_args.extend(["-e", env])
		self._logger.info("Compiling...")
		logs = deque()

		def handle_logs(stream):
			for line in stream:
				self._logger.info(line.rstrip())
				logs.append(line)
		result = self.__exec(pio_args, handle_logs, handle_logs)
		if not result:
			self._logger.warning("Compilation failed")
			self._flash_status = dict(
				step_name=gettext("Compilation failed"),
				progress=100,
				finished=True,
				success=False,
				error_output="".join(logs),
				message=gettext("Compilation failed")
			)
			self._push_flash_status("platformio_flash_status")
			return
		self._logger.info("Compilation success")
		self._flash_status = dict(
			step_name=gettext("Uploading"),
			progress=50,
			finished=False
		)
		self._push_flash_status("platformio_flash_status")
		transport = self._printer.get_transport()
		if not isinstance(transport, serial.Serial):
			self._logger.warning("The printer is not connected via a serial port")
			self._flash_status = dict(
				step_name=gettext("Upload failed"),
				progress=100,
				finished=True,
				success=False,
				message=gettext("The printer is not connected through a Serial port and thus, cannot be flashed.")
			)
			self._push_flash_status("platformio_flash_status")
			return
		self._run_pre_flash_script()
		self._wait_pre_flash_delay()
		_, port, baudrate, profile = self._printer.get_current_connection()
		self._logger.info("Disconnecting printer...")
		self._printer.disconnect()
		self._logger.info("Uploading to the board...")
		pio_args.extend(["-t", "upload"])
		logs.clear()
		result = self.__exec(pio_args, handle_logs, handle_logs)
		if not result:
			self._logger.warning("The flashing process failed!")
			self._printer.connect(port, baudrate, profile)
			self._flash_status = dict(
				step_name=gettext("Upload failed"),
				progress=100,
				finished=True,
				success=False,
				message=gettext("The upload process failed"),
				error_output="".join(logs)
			)
			self._push_flash_status("platformio_flash_status")
			return
		self._logger.info("Uploading success")
		self._wait_post_flash_delay()
		self._should_run_post_script = True
		self._printer.connect(port, baudrate, profile)
		self._firmware = None
		self._firmware_version = None
		self._firmware_author = None
		self._firmware_upload_time = None
		self._push_firmware_info()
		self._flash_status = dict(
			step_name=gettext("Done"),
			progress=100,
			finished=True,
			success=True,
			message=gettext("Board successfully flashed.")
		)
		self._push_flash_status("platformio_flash_status")

	def __get_available_environments(self):
		if self._firmware is None:
			return []
		try:
			self._logger.debug("Trying to open Configuration.h")
			with open(os.path.join(self._firmware, "Marlin", "Configuration.h"), "r") as configuration_h:
				configuration_h_content = configuration_h.read()
				match = re.search(r"^\s*?#define\s+?MOTHERBOARD\s+?(\S*?)\s*?$", configuration_h_content, re.MULTILINE)
				if not match:
					return []
				# Removes the BOARD_ part of the name
				self._logger.debug("Found motherboard %s" % match.group(1))
				motherboard = match.group(1)[6:]
				self._logger.debug("Trying to open pins.h")
				with open(os.path.join(self._firmware, "Marlin", "src", "pins", "pins.h"), "r") as pins_h:
					pins_h_content = pins_h.read()
					match = re.search(r"^\s*?#(el)?if\s+?MB\([^)]*?%s[^)]*?\)\s*?\n.*?(env:.*?)\s*?$" % re.escape(motherboard), pins_h_content, re.MULTILINE)
					if not match:
						return []
					self._logger.debug("Found environments %s" % match.group(2))
					envs = [env[4:] for env in match.group(2).strip().split(" ") if env.startswith("env:")]
					return envs
		except (OSError, IOError) as _:
			# Files are not where they should, maybe it's not Marlin... No env found, the user will select the default one
			self._logger.debug("Could not open file")
			return []

	def _firmware_info_event_name(self):
		return "platformio_firmware_info"

	def __push_available_environments(self):
		self._plugin_manager.send_plugin_message(self._identifier, dict(
			type="platformio_environments",
			result=self.__get_available_environments()
		))

	def __push_last_flash_option(self):
		self._logger.debug("Pushing last flash options through websocket...")
		self._plugin_manager.send_plugin_message(self._identifier, dict(
			type="platformio_last_flash_options",
			options=self._settings.get_platformio_last_flash_options()
		))

	def _push_firmware_info(self):
		BaseFlasher._push_firmware_info(self)
		self.__push_available_environments()

	def send_initial_state(self):
		BaseFlasher.send_initial_state(self)
		self.__push_last_flash_option()
		self._push_flash_status("platformio_flash_status")
		self.__push_login_status()
		self.__push_remote_agent_status()

	def login(self):
		self._logger.debug("Signing in to a PlatformioIO account")
		pio_args = [self._settings.get_platformio_cli_path(), "account", "login", "--username", flask.request.values["username"], "--password", flask.request.values["password"]]
		logs = []

		def handle_logs(stream):
			for line in stream:
				l = line.rstrip()
				self._logger.debug(l)
				logs.append(l)
		success = self.__exec(pio_args, handle_logs, handle_logs, show_in_logs=False)
		if not success:
			self._logger.debug("Connection failed !")
			return None, logs
		self._logger.info("Successfully signed in to the PlatformIO account")
		self.__push_login_status()
		return logs, None

	def logout(self):
		self._logger.debug("Logging out of a PlatformioIO account")
		pio_args = [self._settings.get_platformio_cli_path(), "account", "logout"]
		logs = []

		def handle_logs(stream):
			for line in stream:
				l = line.rstrip()
				self._logger.debug(l)
				logs.append(l)
		success = self.__exec(pio_args, handle_logs, handle_logs)
		if not success:
			self._logger.debug("Logout failed !")
			return None, logs
		self._logger.info("Successfully logged out")
		self.__push_login_status()
		return logs, None

	def __push_login_status(self):
		self._logger.debug("Checking login status...")
		pio_args = [self._settings.get_platformio_cli_path(), "account", "show", "--json-output"]
		logs = deque()

		def handle_logs(stream):
			for line in stream:
				logs.append(line.rstrip())
		success = self.__exec(pio_args, handle_logs, handle_logs)
		if not success:
			message = dict(
				type="platformio_login_status",
				account=None
			)
			self._logger.debug("Could not get account information, we are not logged in")
		else:
			self._logger.debug("Got valid answer, we are logged in")
			account = json.loads("".join(logs))
			message =  dict(
				type="platformio_login_status",
				account=account
			)
		self._plugin_manager.send_plugin_message(self._identifier, message)

	def __push_remote_agent_status(self):
		self._plugin_manager.send_plugin_message(self._identifier, dict(
			type="platformio_remote_agent_status",
			status=self.__remote_agent.get_status()
		))

	def __push_remote_agent_log(self, log):
		self._plugin_manager.send_plugin_message(self._identifier, dict(
			type="platformio_remote_agent_log",
			content=log
		))

