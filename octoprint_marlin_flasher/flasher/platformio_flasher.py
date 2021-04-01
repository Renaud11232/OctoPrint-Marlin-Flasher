from .base_flasher import BaseFlasher
from .flasher_error import FlasherError
from subprocess import Popen, PIPE
import zipfile
import os
import shutil
import re
import json
from threading import Thread
from datetime import datetime
import serial
import flask
from flask_babel import gettext


class PlatformIOFlasher(BaseFlasher):

	def __exec(self, args):
		command = [self._settings.get_platformio_cli_path()]
		command.extend(args)
		try:
			self._logger.debug("Executing command : %s" % " ".join(command))
			p = Popen(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
			stdout, stderr = p.communicate()
			stdout = stdout.strip()
			stderr = stderr.strip()
			self._logger.debug("Return code : %d" % p.returncode)
			self._logger.debug("Standard output : %s" % stdout)
			self._logger.debug("Error output : %s" % stderr)
			if p.returncode != 0:
				raise FlasherError(stderr)
			return stdout
		except OSError:
			self._logger.debug("The executable does not exist")
			raise FlasherError(gettext("The given executable does not exist."))

	def check_setup_errors(self):
		self._logger.debug("Checking PlatformIO configuration...")
		no_platformio_path = self._settings.get_platformio_cli_path() is None
		if no_platformio_path:
			self._logger.info("No PlatformIO path was configured")
			return dict(
				error=gettext("No path has been configured, check the plugin settings.")
			)
		try:
			bad_exec = "platformio" not in self.__exec(["--version"]).lower()
		except FlasherError:
			bad_exec = True
		if bad_exec:
			self._logger.info("The configured path does not point to PlatformIO-Core")
			return dict(
				error=gettext("The configured path does not point to PlatformIO-Core.")
			)
		return None

	def _validate_firmware_file(self, file_path):
		self._logger.debug("Validating firmware file...")
		try:
			with zipfile.ZipFile(file_path, "r") as _:
				return None
		except zipfile.BadZipfile:
			self._logger.debug("The firmware file does not have a valid file type")
			return dict(
				error=gettext("Invalid file type.")
			)

	def _handle_firmware_file(self, firmware_file_path):
		self._firmware = None
		self._firmware_version = None
		self._firmware_author = None
		self._firmware_upload_time = None
		self._logger.debug("Trying to open firmware as zip file...")
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
					elif f == "Version.h":
						self._logger.debug("Found Version.h, opening it...")
						with open(os.path.join(root, f), "r") as versionfile:
							for line in versionfile:
								if "SHORT_BUILD_VERSION" in line:
									self._logger.debug("Found SHORT_BUILD_VERSION")
									version = re.findall('"([^"]*)"', line)
									if version:
										self._firmware_version = version[0]
										break
					elif f == "Configuration.h":
						self._logger.debug("Found Configuration.h, opening it...")
						with open(os.path.join(root, f), "r") as configfile:
							for line in configfile:
								if "STRING_CONFIG_H_AUTHOR" in line:
									self._logger.debug("Found STRING_CONFIG_H_AUTHOR")
									author = re.findall('"([^"]*)"', line)
									if author:
										self._firmware_author = author[0]
										break
			if self._firmware:
				return dict(
					path=self._firmware,
					file="platformio.ini"
				), None
			return None, dict(
				error=gettext("No PlatformIO configuration file were found in the given file.")
			)

	def firmware(self):
		return dict(
			firmware=self._firmware,
			version=self._firmware_version,
			author=self._firmware_author,
			upload_time=self._firmware_upload_time
		), None

	def board_details(self):
		if self._firmware is None:
			return [], None
		try:
			self._logger.debug("Trying to open Configuration.h")
			with open(os.path.join(self._firmware, "Marlin", "Configuration.h"), "r") as configuration_h:
				configuration_h_content = configuration_h.read()
				match = re.search(r"^[ \t]*#define[ \t]+MOTHERBOARD[ \t]+(\S*?)[ \t]*\r?$", configuration_h_content, re.MULTILINE)
				if not match:
					return [], None
				# Removes the BOARD_ part of the name
				self._logger.debug("Found motherboard %s" % match.group(1))
				motherboard = match.group(1)[6:]
				self._logger.debug("Trying to open pins.h")
				with open(os.path.join(self._firmware, "Marlin", "src", "pins", "pins.h"), "r") as pins_h:
					pins_h_content = pins_h.read()
					match = re.search(r"^[ \t]*#(el)?if[ \t]+MB\(%s\)[ \t]*\r?\n.*?(env:.*?)[ \t]*\r?$" % re.escape(motherboard), pins_h_content, re.MULTILINE)
					if not match:
						return [], None
					self._logger.debug("Found environments %s" % match.group(2))
					envs = [env.split(":")[1] for env in match.group(2).split(" ") if env.startswith("env:")]
					return envs, None
		except (OSError, IOError) as _:
			# Files are not where they should, maybe it's not Marlin... No env found, the user will select the default one
			self._logger.debug("Could not open file")
			return [], None

	def flash(self):
		if self._firmware is None:
			self._logger.debug("No firmware uploaded")
			return None, dict(
				error=gettext("You did not upload the firmware or it got reset by the previous flash process.")
			)
		if not self._printer.is_ready():
			self._logger.debug("Printer not ready")
			return None, dict(
				error=gettext("The printer may not be connected or it may be busy.")
			)
		env = None
		if "env" in flask.request.values and flask.request.values["env"]:
			env = flask.request.values["env"]
		thread = Thread(target=self.__background_flash, args=(env,))
		thread.start()
		self._logger.debug("Saving options")
		try:
			with open(os.path.join(self._plugin.get_plugin_data_folder(), "last_options_platformio.json"), "w") as output:
				json.dump(flask.request.values, output)
		except (OSError, IOError) as _:
			pass
		return dict(
			message=gettext("Flash process started.")
		), None

	def __background_flash(self, env):
		self._logger.info("Starting flashing process...")
		disconnected = False
		try:
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="flash_progress",
				step=gettext("Compiling"),
				progress=0
			))
			pio_args = ["run", "-d", self._firmware]
			if env:
				pio_args.extend(["-e", env])
			self._logger.info("Compiling...")
			self.__exec(pio_args)
			self._logger.info("Compilation success")
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="flash_progress",
				step=gettext("Uploading"),
				progress=50
			))
			transport = self._printer.get_transport()
			if not isinstance(transport, serial.Serial):
				self._logger.warning("The printer is not connected via a serial port")
				self._plugin_manager.send_plugin_message(self._identifier, dict(
					type="flash_result",
					success=False,
					error=gettext("The printer is not connected through a Serial port and thus, cannot be flashed.")
				))
				return
			self._run_pre_flash_script()
			self._wait_pre_flash_delay()
			_, port, baudrate, profile = self._printer.get_current_connection()
			self._logger.info("Disconnecting printer...")
			self._printer.disconnect()
			disconnected = True
			self._logger.info("Uploading to the board...")
			pio_args.extend(["-t", "upload"])
			self.__exec(pio_args)
			self._logger.info("Uploading success")
			self._wait_post_flash_delay()
			self._should_run_post_script = True
			self._printer.connect(port, baudrate, profile)
			self._firmware = None
			self._firmware_version = None
			self._firmware_author = None
			self._firmware_upload_time = None
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="flash_progress",
				step=gettext("Done"),
				progress=100
			))
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="flash_result",
				success=True,
				message=gettext("Board successfully flashed.")
			))
		except FlasherError as e:
			self._logger.warning("The flashing process failed!")
			for log_line in e.message.splitlines():
				self._logger.warning(log_line)
			if disconnected:
				self._printer.connect(port, baudrate, profile)
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="flash_result",
				success=False,
				error=gettext("The flashing process failed"),
				stderr=e.message
			))

	def last_flash_options(self):
		try:
			with open(os.path.join(self._plugin.get_plugin_data_folder(), "last_options_platformio.json"), "r") as jsonfile:
				return json.load(jsonfile), None
		except (OSError, IOError) as _:
			return dict(), None
