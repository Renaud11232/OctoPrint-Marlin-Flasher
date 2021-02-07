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


class ArduinoFlasher(BaseFlasher):

	def __init__(self, settings, printer, plugin, plugin_manager, identifier):
		BaseFlasher.__init__(self, settings, printer, plugin, plugin_manager, identifier)
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
		no_arduino_path = self._settings.get_arduino_cli_path() is None
		if no_arduino_path:
			return dict(
				error=gettext("No path has been configured, check the plugin settings.")
			)
		not_arduino = False
		bad_version = False
		try:
			version = self.__get_arduino().version()
			if isinstance(version, dict):
				bad_version = re.match(r"(?:0\.(?:15)\..+?)\Z", version["VersionString"]) is None
			else:
				not_arduino = True
		except pyduinocli.ArduinoError:
			not_arduino = True
		except KeyError:
			bad_version = True
		if not_arduino:
			return dict(
				error=gettext("The configured path does not point to an arduino-cli executable.")
			)
		if bad_version:
			return dict(
				error=gettext("The arduino-cli version you are using is not supported.")
			)
		return None

	def upload(self):
		self._firmware = None
		self._firmware_version = None
		self._firmware_author = None
		self._firmware_upload_time = None
		uploaded_file_path = flask.request.values["firmware_file." + self._settings.get_upload_path_suffix()]
		firmware_dir = os.path.join(self._plugin.get_plugin_data_folder(), "firmware_arduino")
		if os.path.exists(firmware_dir):
			shutil.rmtree(firmware_dir)
		try:
			with zipfile.ZipFile(uploaded_file_path, "r") as zip_file:
				self.__is_ino = True
				sketch_dir = os.path.join(firmware_dir, os.path.splitext(self._settings.get_arduino_sketch_ino())[0])
				os.makedirs(sketch_dir)
				zip_file.extractall(sketch_dir)
				for root, dirs, files in os.walk(sketch_dir):
					for f in files:
						if f == self._settings.get_arduino_sketch_ino():
							self._firmware = root
							self._firmware_upload_time = datetime.now()
						elif f == "Version.h":
							with open(os.path.join(root, f), "r") as versionfile:
								for line in versionfile:
									if "SHORT_BUILD_VERSION" in line:
										version = re.findall('"([^"]*)"', line)
										if version:
											self._firmware_version = version[0]
											break
						elif f == "Configuration.h":
							with open(os.path.join(root, f), "r") as configfile:
								for line in configfile:
									if "STRING_CONFIG_H_AUTHOR" in line:
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
			self.__is_ino = False
			os.makedirs(firmware_dir)
			self._firmware = os.path.join(firmware_dir, "firmware.hex")
			self._firmware_upload_time = datetime.now()
			shutil.copyfile(uploaded_file_path, self._firmware)
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
			arduino.core.update_index()
			result = arduino.core.search(flask.request.values["query"].split(" "))
			return result, None
		except pyduinocli.ArduinoError as e:
			return None, self.__error_to_dict(e)

	def lib_search(self):
		try:
			arduino = self.__get_arduino()
			arduino.core.update_index()
			result = arduino.lib.search(flask.request.values["query"].split(" "))
			return result, None
		except pyduinocli.ArduinoError as e:
			return None, self.__error_to_dict(e)

	def core_install(self):
		try:
			arduino = self.__get_arduino()
			arduino.core.install([flask.request.values["core"]])
			return dict(
				core=flask.request.values["core"]
			), None
		except pyduinocli.ArduinoError as e:
			return None, self.__error_to_dict(e)

	def lib_install(self):
		try:
			arduino = self.__get_arduino()
			arduino.lib.install([flask.request.values["lib"]])
			return dict(
				lib=flask.request.values["lib"]
			), None
		except pyduinocli.ArduinoError as e:
			return None, self.__error_to_dict(e)

	def core_uninstall(self):
		try:
			arduino = self.__get_arduino()
			arduino.core.uninstall([flask.request.values["core"]])
			return dict(
				core=flask.request.values["core"]
			), None
		except pyduinocli.ArduinoError as e:
			return None, self.__error_to_dict(e)

	def lib_uninstall(self):
		try:
			arduino = self.__get_arduino()
			# TODO this is not needed for versions >= 0.7.0
			arduino.lib.uninstall([flask.request.values["lib"].replace(" ", "_")])
			return dict(
				lib=flask.request.values["lib"]
			), None
		except pyduinocli.ArduinoError as e:
			return None, self.__error_to_dict(e)

	def board_listall(self):
		try:
			arduino = self.__get_arduino()
			arduino.core.update_index()
			result = arduino.board.listall()
			return result, None
		except pyduinocli.ArduinoError as e:
			return None, self.__error_to_dict(e)

	def board_details(self):
		try:
			arduino = self.__get_arduino()
			result = arduino.board.details(flask.request.values["fqbn"])
			return result, None
		except pyduinocli.ArduinoError as e:
			return None, self.__error_to_dict(e)

	def flash(self):
		if self._firmware is None:
			return None, dict(
				error=gettext("You did not upload the firmware or it got reset by the previous flash process.")
			)
		if not self._printer.is_ready():
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
		try:
			with open(os.path.join(self._plugin.get_plugin_data_folder(), "last_options_arduino.json"), "w") as output:
				json.dump(flask.request.values, output)
		except (OSError, IOError) as _:
			pass
		return dict(
			message=gettext("Flash process started.")
		), None

	def __background_flash(self, fqbn):
		try:
			arduino = self.__get_arduino()
			if self.__is_ino:
				self._plugin_manager.send_plugin_message(self._identifier, dict(
					type="flash_progress",
					step=gettext("Compiling"),
					progress=0
				))
				arduino.compile(self._firmware, fqbn=fqbn)
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
			self._printer.disconnect()
			if self.__is_ino:
				arduino.upload(sketch=self._firmware, fqbn=fqbn, port=flash_port)
			else:
				arduino.upload(fqbn=fqbn, port=flash_port, input_file=self._firmware)
			self._wait_post_flash_delay()
			self._printer.connect(port, baudrate, profile)
			self._firmware = None
			self._firmware_version = None
			self._firmware_author = None
			self._firmware_upload_time = None
			self._should_run_post_script = True
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
