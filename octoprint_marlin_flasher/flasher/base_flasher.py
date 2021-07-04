from .flasher_error import FlasherError
import time
import flask
import requests
import tempfile
import os
import re
from threading import Thread


class BaseFlasher:

	def __init__(self, settings, printer, plugin, plugin_manager, identifier, logger):
		self._settings = settings
		self._printer = printer
		self._plugin = plugin
		self._plugin_manager = plugin_manager
		self._identifier = identifier
		self._logger = logger
		self._firmware = None
		self._firmware_version = None
		self._firmware_author = None
		self._firmware_upload_time = None
		self._should_run_post_script = False

	def _background_run(self, target, args=None):
		thread = Thread(target=target, args=args)
		thread.start()
		return thread

	def _run_pre_flash_script(self):
		pre_flash_script = self._settings.get_pre_flash_script()
		if pre_flash_script:
			self._logger.debug("Running pre-flash GCode script :")
			self._logger.debug(pre_flash_script)
			commands = [line.strip() for line in pre_flash_script.splitlines()]
			self._printer.commands(commands)
		else:
			self._logger.debug("No pre-flash GCode script defined")

	def _wait_pre_flash_delay(self):
		self._logger.debug("Waiting pre-flash delay...")
		time.sleep(self._settings.get_pre_flash_delay())

	def _run_post_flash_script(self):
		post_flash_script = self._settings.get_post_flash_script()
		if post_flash_script:
			self._logger.debug("Running post-flash script")
			self._logger.debug(post_flash_script)
			commands = [line.strip() for line in post_flash_script.splitlines()]
			self._printer.commands(commands)
		else:
			self._logger.debug("No script defined")

	def _wait_post_flash_delay(self):
		self._logger.debug("Waiting post-flash delay...")
		time.sleep(self._settings.get_post_flash_delay())

	def _validate_firmware_file(self, file_path):
		raise FlasherError("Unsupported function call.")

	def handle_connected_event(self):
		if self._should_run_post_script:
			self._run_post_flash_script()
			self._should_run_post_script = False

	# def check_setup_errors(self):
	# 	raise FlasherError("Unsupported function call.")

	def upload(self):
		self._logger.debug("Firmware uploaded by the user")
		uploaded_file_path = flask.request.values["firmware_file." + self._settings.get_upload_path_suffix()]
		errors = self._validate_firmware_file(uploaded_file_path)
		if errors:
			self._push_firmware_info()
			return None, errors
		result = self._handle_firmware_file(uploaded_file_path)
		self._push_firmware_info()
		return result

	def download(self):
		self._logger.debug("Downloading firmware...")
		r = requests.get(flask.request.values["url"])
		self._logger.debug("Saving downloaded firmware...")
		with tempfile.NamedTemporaryFile(delete=False) as temp:
			temp.write(r.content)
			temp_path = temp.name
		errors = self._validate_firmware_file(temp_path)
		if errors:
			self._push_firmware_info()
			os.remove(temp_path)
			return None, errors
		result = self._handle_firmware_file(temp_path)
		self._push_firmware_info()
		self._logger.debug("Clearing downloaded firmware...")
		os.remove(temp_path)
		return result

	def _handle_firmware_file(self, firmware_file_path):
		raise FlasherError("Unsupported function call.")

	def _find_firmware_info(self):
		for root, dirs, files in os.walk(self._firmware):
			for f in files:
				if f == "Version.h":
					self._logger.debug("Found Version.h, opening it...")
					with open(os.path.join(root, f), "r") as versionfile:
						for line in versionfile:
							version = re.findall(r'#define +SHORT_BUILD_VERSION +"([^"]*)"', line)
							if version:
								self._firmware_version = version[0]
								self._logger.debug("Found SHORT_BUILD_VERSION : %s" % self._firmware_version)
								break
				elif f == "Configuration.h":
					self._logger.debug("Found Configuration.h, opening it...")
					with open(os.path.join(root, f), "r") as configfile:
						for line in configfile:
							author = re.findall(r'#define +STRING_CONFIG_H_AUTHOR +"([^"]*)"', line)
							if author:
								self._firmware_author = author[0]
								self._logger.debug("Found STRING_CONFIG_H_AUTHOR : %s" % self._firmware_author)
								break

	def _push_firmware_info(self):
		self._logger.debug("Sending firmware info through websocket")
		self._plugin_manager.send_plugin_message(self._identifier, dict(
			type="firmware_info",
			version=self._firmware_version,
			author=self._firmware_author,
			upload_time=self._firmware_upload_time.strftime("%d/%m/%Y, %H:%M:%S") if self._firmware_upload_time is not None else None,
			firmware=self._firmware
		))

	def send_initial_state(self):
		self._push_firmware_info()
