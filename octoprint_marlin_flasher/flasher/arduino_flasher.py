import platform

from .base_flasher import BaseFlasher
import zipfile
import re
import os
import shutil
from threading import Thread
from datetime import datetime
import serial
import flask
from flask_babel import gettext
import pyduinocli
import intelhex
import requests
import tarfile
import io


class ArduinoFlasher(BaseFlasher):

	def __init__(self, settings, printer, plugin, plugin_manager, identifier, logger):
		BaseFlasher.__init__(self, settings, printer, plugin, plugin_manager, identifier, logger)
		self.__is_ino = False

	def start_install(self):
		self._logger.info("Starting the installation of arduino-cli")
		system = platform.system()
		self._logger.debug("platform.system() is %s" % system)
		system_os_map = {
			"Linux": "Linux",
			"Windows": "Windows",
			"Darwin": "macOS"
		}
		if system not in system_os_map:
			self._logger.warning("Unknown system %s" % system)
			return None, [gettext("Unable to detect OS : ") + system]
		os = system_os_map[system]
		os_ext_map = {
			"Linux": "tar.gz",
			"Windows": "zip",
			"macOS": "tar.gz"
		}
		ext = os_ext_map[os]
		machine = platform.machine()
		self._logger.debug("platform.machine() is %s" % machine)
		machine_arch_map = {
			"AMD64": "64bit",
			"i386": "32bit",
			"armv7l": "ARMv7",
			"armv6l": "ARMv6"
		}
		if machine not in machine_arch_map:
			self._logger.warning("Unknown machine %s" % machine)
			return None, [gettext("Unable to detect architecture : ") + machine]
		arch = machine_arch_map[machine]
		self._background_run(self.__install, args=(os, arch, ext))
		return dict(
			message=gettext("The installation of arduino-cli is started")
		), None

	def __install(self, operating_system, arch, ext):
		installation_path = os.path.join(self._plugin.get_plugin_data_folder(), "arduino-cli")
		installed_version = "0.22.0"
		url = "https://github.com/arduino/arduino-cli/releases/download/{version}/arduino-cli_{version}_{os}_{arch}.{ext}"
		download_url = url.format(version=installed_version, os=operating_system, arch=arch, ext=ext)
		self._logger.info("Downloading %s" % download_url)
		self._plugin_manager.send_plugin_message(self._identifier, dict(
			type="arduino_install",
			finished=False,
			status=gettext("Downloading %s") % download_url
		))
		try:
			r = requests.get(download_url)
		except requests.exceptions.RequestException:
			self._logger.warning("Failed to download %s" % download_url)
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="arduino_install",
				finished=True,
				success=False,
				status=gettext("Failed to download %s") % download_url
			))
			return
		if os.path.exists(installation_path):
			self._logger.info("Previous installation found in %s, removing it" % installation_path)
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="arduino_install",
				finished=False,
				status=gettext("Previous installation found in %s, removing it") % installation_path
			))
			shutil.rmtree(installation_path)
		try:
			if ext == "zip":
				file = zipfile.ZipFile(io.BytesIO(r.content), "r")
			else:
				file = tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz")
			with file as archive:
				self._logger.info("Extracting in %s" % installation_path)
				self._plugin_manager.send_plugin_message(self._identifier, dict(
					type="arduino_install",
					finished=False,
					status=gettext("Extracting in %s") % installation_path
				))
				archive.extractall(installation_path)
				if operating_system == "Windows":
					executable_name = "arduino-cli.exe"
				else:
					executable_name = "arduino-cli"
				executable_path = os.path.join(installation_path, executable_name)
				self._logger.info("Successfully installed arduino-cli in %s" % installation_path)
				self._plugin_manager.send_plugin_message(self._identifier, dict(
					type="arduino_install",
					finished=True,
					success=True,
					path=executable_path,
					status=gettext("Successfully installed arduino-cli in %s") % installation_path
				))
		except:
			self._logger.warning("Failed to extract downloaded archive")
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="arduino_install",
				finished=True,
				success=False,
				status=gettext("Failed to extract downloaded archive")
			))

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
				return [gettext("Invalid file type.")]

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
				if self._firmware:
					self._find_firmware_info()
					return dict(
						path=self._firmware,
						file=self._settings.get_arduino_sketch_ino()
					), None
				return None, [gettext("No valid sketch were found in the given file.")]
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

	def __get_arduino(self):
		path = self._settings.get_arduino_cli_path()
		additional_urls = self._settings.get_arduino_additional_urls()
		if additional_urls:
			additional_urls = additional_urls.splitlines()
		return pyduinocli.Arduino(path, additional_urls=additional_urls)

	def check_setup_errors(self):
		self._logger.debug("Checking arduino-cli configuration...")
		no_arduino_path = self._settings.get_arduino_cli_path() is None
		if no_arduino_path:
			self._logger.info("No arduino-cli path was configured")
			return [gettext("No path has been configured, check the plugin settings.")]
		not_arduino = False
		bad_version = False
		try:
			version = self.__get_arduino().version()["result"]
			if isinstance(version, dict):
				bad_version = re.match(r"0\.(?:18|19|20|21|22)\..+?\Z", version["VersionString"]) is None
			else:
				not_arduino = True
		except pyduinocli.ArduinoError:
			not_arduino = True
		except OSError:
			not_arduino = True
		except KeyError:
			bad_version = True
		if not_arduino:
			self._logger.info("The configured path is not an arduino-cli executable")
			return [gettext("The configured path does not point to an arduino-cli executable.")]
		if bad_version:
			self._logger.info("Unsupported arduino-cli version")
			return [gettext("The arduino-cli version you are using is not supported.")]
		return []

	def core_search(self):
		try:
			arduino = self.__get_arduino()
			self._logger.debug("Searching for cores...")
			result = arduino.core.search(flask.request.values["query"].split(" "))["result"]
			self._logger.debug("Done")
			return result, None
		except pyduinocli.ArduinoError as e:
			self._logger.debug("Failed !")
			return None, [e.result["__stderr"]]

	def core_install(self):
		try:
			arduino = self.__get_arduino()
			self._logger.debug("Installing core...")
			arduino.core.install([flask.request.values["core"]])
			self._logger.debug("Done")
			self.__push_installed_boards()
			return dict(
				core=flask.request.values["core"]
			), None
		except pyduinocli.ArduinoError as e:
			self._logger.debug("Failed !")
			return None, [e.result["__stderr"]]

	def core_uninstall(self):
		try:
			arduino = self.__get_arduino()
			self._logger.debug("Uninstalling core...")
			arduino.core.uninstall([flask.request.values["core"]])
			self._logger.debug("Done")
			self.__push_installed_boards()
			return dict(
				core=flask.request.values["core"]
			), None
		except pyduinocli.ArduinoError as e:
			self._logger.debug("Failed !")
			return None, [e.result["__stderr"]]

	def lib_search(self):
		try:
			arduino = self.__get_arduino()
			self._logger.debug("Searching for libraries...")
			result = arduino.lib.search(flask.request.values["query"].split(" "))["result"]
			self._logger.debug("Done")
			return result, None
		except pyduinocli.ArduinoError as e:
			self._logger.debug("Failed !")
			return None, [e.result["__stderr"]]

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
			return None, [e.result["__stderr"]]

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
			return None, [e.result["__stderr"]]

	def board_details(self):
		try:
			arduino = self.__get_arduino()
			self._logger.debug("Getting board details...")
			result = arduino.board.details(flask.request.values["fqbn"])["result"]
			self._logger.debug("Done")
			return result, None
		except pyduinocli.ArduinoError as e:
			self._logger.debug("Failed !")
			return None, [e.result["__stderr"]]

	def flash(self):
		if self._firmware is None:
			self._logger.debug("No firmware uploaded")
			return None, [gettext("You did not upload the firmware or it got reset by the previous flash process.")]
		if not self._printer.is_ready():
			self._logger.debug("Printer not ready")
			return None, [gettext("The printer may not be connected or it may be busy.")]
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
		self._settings.set_arduino_last_flash_options(flask.request.values.to_dict())
		self._settings.save()
		self.__push_last_flash_option()
		return dict(
			message=gettext("Flash process started.")
		), None

	def __background_flash(self, fqbn):
		self._logger.info("Starting flashing process...")
		disconnected = False
		try:
			arduino = self.__get_arduino()
			if self.__is_ino:
				self._flash_status = dict(
					step_name=gettext("Compiling"),
					progress=0,
					finished=False
				)
				self._push_flash_status("arduino_flash_status")
				self._logger.info("Compiling...")
				result = arduino.compile(self._firmware, fqbn=fqbn)
				if not result["result"]["success"]:
					self._logger.warning("Compilation failed")
					self._logger.warning("Standard output :")
					for log_line in result["result"]["compiler_out"].splitlines():
						self._logger.warning(log_line)
					self._logger.warning("Error output :")
					# TODO fix the error output when arduino-cli will be fixed...
					error = result["result"]["compiler_err"] if result["result"]["compiler_err"] else result["__stderr"]
					for log_line in error.splitlines():
						self._logger.warning(log_line)
					self._flash_status = dict(
						step_name=gettext("Compilation failed"),
						progress=100,
						finished=True,
						success=False,
						error_output=error,
						message=result["result"]["compiler_out"]
					)
					self._push_flash_status("arduino_flash_status")
					return
				self._logger.info("Compilation success")
				self._flash_status = dict(
					step_name=gettext("Uploading"),
					progress=50,
					finished=False
				)
				self._push_flash_status("arduino_flash_status")
			else:
				self._flash_status = dict(
					step_name=gettext("Uploading"),
					progress=0,
					finished=False
				)
				self._push_flash_status("arduino_flash_status")
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
				self._push_flash_status("arduino_flash_status")
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
			self._push_firmware_info()
			self._flash_status = dict(
				step_name=gettext("Done"),
				progress=100,
				finished=True,
				success=True,
				message=gettext("Board successfully flashed.")
			)
			self._push_flash_status("arduino_flash_status")
		except pyduinocli.ArduinoError as e:
			self._logger.warning("Error : %s" % e.result["result"])
			self._logger.warning("Error output : ")
			for log_line in e.result["__stderr"].splitlines():
				self._logger.warning(log_line)
			if disconnected:
				self._printer.connect(port, baudrate, profile)
			self._flash_status = dict(
				step_name=gettext("Upload failed"),
				progress=100,
				finished=True,
				success=False,
				message=e.result["result"],
				error_output=e.result["__stderr"]
			)
			self._push_flash_status("arduino_flash_status")

	def __push_installed_boards(self):
		if self.check_setup_errors():
			return
		try:
			arduino = self.__get_arduino()
			self._logger.debug("Listing installed boards...")
			result = arduino.board.listall()["result"]
			self._logger.debug("Done")
			self._logger.debug("Pushing installed boards through websocket ")
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="arduino_boards",
				result=result
			))
		except pyduinocli.ArduinoError as e:
			self._logger.debug("Failed to push the list of installed boards")
			self._logger.debug(e.result["__stderr"])

	def _firmware_info_event_name(self):
		return "arduino_firmware_info"

	def __push_last_flash_option(self):
		self._logger.debug("Pushing last flash options through websocket...")
		self._plugin_manager.send_plugin_message(self._identifier, dict(
			type="arduino_last_flash_options",
			options=self._settings.get_arduino_last_flash_options()
		))

	def send_initial_state(self):
		BaseFlasher.send_initial_state(self)
		self.__push_installed_boards()
		self.__push_last_flash_option()
		self._push_flash_status("arduino_flash_status")
