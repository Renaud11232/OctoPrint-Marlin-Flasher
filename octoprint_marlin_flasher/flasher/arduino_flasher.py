from .base_flasher import BaseFlasher
import zipfile
import re
import os
import shutil
import json
from threading import Thread
from datetime import datetime
import serial
import flask
from flask_babel import gettext
import pyduinocli
import intelhex


class ArduinoFlasher(BaseFlasher):

	def __init__(self, settings, printer, plugin, plugin_manager, identifier, logger):
		BaseFlasher.__init__(self, settings, printer, plugin, plugin_manager, identifier, logger)
		self.__is_ino = False

	def __get_arduino(self):
		path = self._settings.get_arduino_cli_path()
		additional_urls = self._settings.get_arduino_additional_urls()
		if additional_urls:
			additional_urls = additional_urls.splitlines()
		return pyduinocli.Arduino(path, additional_urls=additional_urls)

	@staticmethod
	def __error_to_dict(error):
		return dict(
			error=error.message,
			cause=error.cause,
			stderr=error.stderr
		)

	def check_setup_errors(self):
		self._logger.debug("Checking arduino-cli configuration...")
		no_arduino_path = self._settings.get_arduino_cli_path() is None
		if no_arduino_path:
			self._logger.info("No arduino-cli path was configured")
			return dict(
				error=gettext("No path has been configured, check the plugin settings.")
			)
		not_arduino = False
		bad_version = False
		try:
			version = self.__get_arduino().version()
			if isinstance(version, dict):
				bad_version = re.match(r"(?:0\.(?:15|16|17|18)\..+?)\Z", version["VersionString"]) is None
			else:
				not_arduino = True
		except pyduinocli.ArduinoError:
			not_arduino = True
		except KeyError:
			bad_version = True
		if not_arduino:
			self._logger.info("The configured path is not an arduino-cli executable")
			return dict(
				error=gettext("The configured path does not point to an arduino-cli executable.")
			)
		if bad_version:
			self._logger.info("Unsupported arduino-cli version")
			return dict(
				error=gettext("The arduino-cli version you are using is not supported.")
			)
		return None

	def _validate_firmware_file(self, file_path):
		self._logger.debug("Validating firmware file, checking for zip...")
		try:
			with zipfile.ZipFile(file_path, "r") as _:
				return None
		except zipfile.BadZipfile:
			self._logger.debug("The firmware is not a zip file, checking if it's a .hex")
			try:
				ih = intelhex.IntelHex()
				ih.loadhex(file_path)
				return None
			except:
				self._logger.debug("The firmware file is not valid")
				return dict(
					error=gettext("Invalid file type.")
				)

	def _handle_firmware_file(self, firmware_file_path):
		self._firmware = None
		self._firmware_version = None
		self._firmware_author = None
		self._firmware_upload_time = None
		firmware_dir = os.path.join(self._plugin.get_plugin_data_folder(), "firmware_arduino")
		if os.path.exists(firmware_dir):
			shutil.rmtree(firmware_dir)
		try:
			self._logger.debug("Trying to open firmware as zip file...")
			with zipfile.ZipFile(firmware_file_path, "r") as zip_file:
				self.__is_ino = True
				sketch_dir = os.path.join(firmware_dir, os.path.splitext(self._settings.get_arduino_sketch_ino())[0])
				os.makedirs(sketch_dir)
				self._logger.debug("Extracting firmware archive...")
				zip_file.extractall(sketch_dir)
				self._logger.debug("Browsing files...")
				for root, dirs, files in os.walk(sketch_dir):
					for f in files:
						if f == self._settings.get_arduino_sketch_ino():
							self._logger.debug("Found .ino file")
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
						file=self._settings.get_arduino_sketch_ino()
					), None
				return None, dict(
					error=gettext("No valid sketch were found in the given file.")
				)
		except zipfile.BadZipfile:
			self._logger.debug("Trying to open firmware as hex file...")
			self.__is_ino = False
			os.makedirs(firmware_dir)
			self._firmware = os.path.join(firmware_dir, "firmware.hex")
			self._firmware_upload_time = datetime.now()
			self._logger.debug("Copying file in plugin directory.")
			shutil.copyfile(firmware_file_path, self._firmware)
			return dict(
				path=firmware_dir,
				file="firmware.hex"
			), None

	def firmware(self):
		return dict(
			firmware=self._firmware,
			version=self._firmware_version,
			author=self._firmware_author,
			upload_time=self._firmware_upload_time
		), None

	def core_search(self):
		try:
			arduino = self.__get_arduino()
			self._logger.debug("Updating core index...")
			arduino.core.update_index()
			self._logger.debug("Searching for cores...")
			result = arduino.core.search(flask.request.values["query"].split(" "))
			self._logger.debug("Done")
			return result, None
		except pyduinocli.ArduinoError as e:
			self._logger.debug("Failed !")
			return None, self.__error_to_dict(e)

	def lib_search(self):
		try:
			arduino = self.__get_arduino()
			self._logger.debug("Updating lib index...")
			arduino.lib.update_index()
			self._logger.debug("Searching for libraries...")
			result = arduino.lib.search(flask.request.values["query"].split(" "))
			self._logger.debug("Done")
			return result, None
		except pyduinocli.ArduinoError as e:
			self._logger.debug("Failed !")
			return None, self.__error_to_dict(e)

	def core_install(self):
		try:
			arduino = self.__get_arduino()
			self._logger.debug("Installing core...")
			arduino.core.install([flask.request.values["core"]])
			self._logger.debug("Done")
			return dict(
				core=flask.request.values["core"]
			), None
		except pyduinocli.ArduinoError as e:
			self._logger.debug("Failed !")
			return None, self.__error_to_dict(e)

	def lib_install(self):
		try:
			arduino = self.__get_arduino()
			self._logger.debug("Installing lib...")
			arduino.lib.install([flask.request.values["lib"]])
			self._logger.debug("Done")
			return dict(
				lib=flask.request.values["lib"]
			), None
		except pyduinocli.ArduinoError as e:
			self._logger.debug("Failed !")
			return None, self.__error_to_dict(e)

	def core_uninstall(self):
		try:
			arduino = self.__get_arduino()
			self._logger.debug("Uninstalling core...")
			arduino.core.uninstall([flask.request.values["core"]])
			self._logger.debug("Done")
			return dict(
				core=flask.request.values["core"]
			), None
		except pyduinocli.ArduinoError as e:
			self._logger.debug("Failed !")
			return None, self.__error_to_dict(e)

	def lib_uninstall(self):
		try:
			arduino = self.__get_arduino()
			self._logger.debug("Uninstalling lib...")
			arduino.lib.uninstall([flask.request.values["lib"]])
			self._logger.debug("Done")
			return dict(
				lib=flask.request.values["lib"]
			), None
		except pyduinocli.ArduinoError as e:
			self._logger.debug("Failed !")
			return None, self.__error_to_dict(e)

	def board_listall(self):
		try:
			arduino = self.__get_arduino()
			self._logger.debug("Updating core index...")
			arduino.core.update_index()
			self._logger.debug("Listing installed boards...")
			result = arduino.board.listall()
			self._logger.debug("Done")
			return result, None
		except pyduinocli.ArduinoError as e:
			self._logger.debug("Failed !")
			return None, self.__error_to_dict(e)

	def board_details(self):
		try:
			arduino = self.__get_arduino()
			self._logger.debug("Getting board details...")
			result = arduino.board.details(flask.request.values["fqbn"])
			self._logger.debug("Done")
			return result, None
		except pyduinocli.ArduinoError as e:
			self._logger.debug("Failed !")
			return None, self.__error_to_dict(e)

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
		options = []
		for param in flask.request.values:
			if param != "fqbn":
				options.append("%s=%s" % (param, flask.request.values[param]))
		options = ",".join(options)
		fqbn = flask.request.values["fqbn"]
		if options:
			fqbn = "%s:%s" % (fqbn, options)
		thread = Thread(target=self.__background_flash, args=(fqbn,))
		thread.start()
		self._logger.debug("Saving options")
		try:
			with open(os.path.join(self._plugin.get_plugin_data_folder(), "last_options_arduino.json"), "w") as output:
				json.dump(flask.request.values, output)
		except (OSError, IOError) as _:
			pass
		return dict(
			message=gettext("Flash process started.")
		), None

	def __background_flash(self, fqbn):
		self._logger.info("Starting flashing process...")
		disconnected = False
		try:
			arduino = self.__get_arduino()
			if self.__is_ino:
				self._plugin_manager.send_plugin_message(self._identifier, dict(
					type="flash_progress",
					step=gettext("Compiling"),
					progress=0
				))
				self._logger.info("Compiling...")
				result = arduino.compile(self._firmware, fqbn=fqbn)
				if not result["success"]:
					self._logger.warning("Compilation failed")
					self._logger.warning("Standard output :")
					for log_line in result["compiler_out"].splitlines():
						self._logger.warning(log_line)
					self._logger.warning("Error output :")
					for log_line in result["compiler_err"].splitlines():
						self._logger.warning(log_line)
					self._plugin_manager.send_plugin_message(self._identifier, dict(
						type="flash_result",
						success=False,
						stderr=result["compiler_err"],
						error=result["compiler_out"]
					))
					return
				self._logger.info("Compilation success")
				self._plugin_manager.send_plugin_message(self._identifier, dict(
					type="flash_progress",
					step=gettext("Uploading"),
					progress=50
				))
			else:
				self._plugin_manager.send_plugin_message(self._identifier, dict(
					type="flash_progress",
					step=gettext("Uploading"),
					progress=0
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
			flash_port = transport.port
			_, port, baudrate, profile = self._printer.get_current_connection()
			self._logger.info("Disconnecting printer...")
			self._printer.disconnect()
			disconnected = True
			self._logger.info("Uploading to the board...")
			if self.__is_ino:
				arduino.upload(sketch=self._firmware, fqbn=fqbn, port=flash_port)
			else:
				arduino.upload(fqbn=fqbn, port=flash_port, input_file=self._firmware)
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
		except pyduinocli.ArduinoError as e:
			self._logger.warning(e.message)
			self._logger.warning("Cause : %s" % e.cause)
			self._logger.warning("Error output : ")
			for log_line in e.stderr.splitlines():
				self._logger.warning(log_line)
			if disconnected:
				self._printer.connect(port, baudrate, profile)
			error = self.__error_to_dict(e)
			error.update(dict(
				type="flash_result",
				success=False
			))
			self._plugin_manager.send_plugin_message(self._identifier, error)

	def last_flash_options(self):
		try:
			with open(os.path.join(self._plugin.get_plugin_data_folder(), "last_options_arduino.json"), "r") as jsonfile:
				return json.load(jsonfile), None
		except (OSError, IOError) as _:
			return dict(), None
