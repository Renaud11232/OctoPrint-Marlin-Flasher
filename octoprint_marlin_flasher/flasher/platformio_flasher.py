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
			p = Popen(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
			stdout, stderr = p.communicate()
			stdout = stdout.strip()
			stderr = stderr.strip()
			if p.returncode != 0:
				raise FlasherError(stderr)
			return stdout
		except OSError:
			raise FlasherError(gettext("The given executable does not exist."))

	def check_setup_errors(self):
		no_platformio_path = self._settings.get_platformio_cli_path() is None
		if no_platformio_path:
			return dict(
				error=gettext("No path has been configured, check the plugin settings.")
			)
		try:
			bad_exec = "platformio" not in self.__exec(["--version"]).lower()
		except FlasherError:
			bad_exec = True
		if bad_exec:
			return dict(
				error=gettext("The configured path does not point to PlatformIO-Core.")
			)
		return None

	def upload(self):
		self._firmware = None
		uploaded_file_path = flask.request.values["firmware_file." + self._settings.get_upload_path_suffix()]
		with zipfile.ZipFile(uploaded_file_path, "r") as zip_file:
			firmware_dir = os.path.join(self._plugin.get_plugin_data_folder(), "firmware_platformio")
			if os.path.exists(firmware_dir):
				shutil.rmtree(firmware_dir)
			os.makedirs(firmware_dir)
			zip_file.extractall(firmware_dir)
			for root, dirs, files in os.walk(firmware_dir):
				for f in files:
					if f == "platformio.ini":
						self._firmware = root
						self._firmware_upload_time = datetime.now()
						return dict(
							path=root,
							file=f
						), None
			return None, dict(
				error=gettext("No Platform.io configuration file were found in the given file.")
			)

	def firmware(self):
		return dict(
			firmware=self._firmware,
			upload_time=self._firmware_upload_time
		), None

	def board_details(self):
		if self._firmware is None:
			return [], None
		try:
			self._plugin._logger.info(os.path.join(self._firmware, "Marlin", "Configuration.h"))
			with open(os.path.join(self._firmware, "Marlin", "Configuration.h"), "r") as configuration_h:
				configuration_h_content = configuration_h.read()
				match = re.search(r"^ *#define +MOTHERBOARD +(.*?) *$", configuration_h_content, re.MULTILINE)
				self._plugin._logger.info(match)
				if not match:
					return [], None
				# Removes the BOARD_ part of the name
				motherboard = match.group(1)[6:]
				self._plugin._logger.info(os.path.join(self._firmware, "Marlin", "src", "pins", "pins.h"))
				with open(os.path.join(self._firmware, "Marlin", "src", "pins", "pins.h"), "r") as pins_h:
					pins_h_content = pins_h.read()
					match = re.search(r"^ *#(el|)if +MB\(%s\) *(\r\n|\n).*?(env:.*?) *$" % motherboard, pins_h_content, re.MULTILINE)
					self._plugin._logger.info(match)
					if not match:
						return [], None
					envs = [env.split(":")[1] for env in match.group(3).split(" ") if env.startswith("env:")]
					return envs, None
		except (OSError, IOError) as _:
			# Files are not where they should, maybe it's not Marlin... No env found, the user will select the default one
			return [], None

	def flash(self):
		if self._firmware is None:
			return None, dict(
				error=gettext("You did not upload the firmware or it got reset by the previous flash process.")
			)
		if not self._printer.is_ready():
			return None, dict(
				error=gettext("The printer may not be connected or it may be busy.")
			)
		env = None
		if "env" in flask.request.values and flask.request.values["env"]:
			env = flask.request.values["env"]
		thread = Thread(target=self.__background_flash, args=(env,))
		thread.start()
		try:
			with open(os.path.join(self._plugin.get_plugin_data_folder(), "last_options_platformio.json"), "w") as output:
				json.dump(flask.request.values, output)
		except (OSError, IOError) as _:
			pass
		return dict(
			message=gettext("Flash process started.")
		), None

	def __background_flash(self, env):
		try:
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="flash_progress",
				step=gettext("Compiling"),
				progress=0
			))
			pio_args = ["run", "-d", self._firmware]
			if env:
				pio_args.extend(["-e", env])
			self.__exec(pio_args)
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="flash_progress",
				step=gettext("Uploading"),
				progress=50
			))
			transport = self._printer.get_transport()
			if not isinstance(transport, serial.Serial):
				self._plugin_manager.send_plugin_message(self._identifier, dict(
					type="flash_result",
					success=False,
					error=gettext("The printer is not connected through a Serial port and thus, cannot be flashed.")
				))
				return
			_, port, baudrate, profile = self._printer.get_current_connection()
			self._printer.disconnect()
			pio_args.extend(["-t", "upload"])
			self.__exec(pio_args)
			self._printer.connect(port, baudrate, profile)
			self._firmware = None
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
