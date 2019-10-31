from .base_flasher import BaseFlasher
import zipfile
import re
import os
import shutil
import flask
from flask_babel import gettext
import pyduinocli


class ArduinoFlasher(BaseFlasher):

	def __init__(self, settings, printer, data_folder):
		BaseFlasher.__init__(self, settings, printer, data_folder)
		self.__is_ino = False

	def __get_arduino(self):
		path = self._settings.get_arduino_cli_path()
		additional_urls = self._settings.get_arduino_additional_urls()
		if additional_urls:
			additional_urls = additional_urls.splitlines()
		return pyduinocli.Arduino(path, additional_urls=additional_urls)

	def check_setup_errors(self):
		no_arduino_path = self._settings.get_arduino_cli_path() is None
		if no_arduino_path:
			return dict(
				error=gettext("No arduino-cli path"),
				cause=gettext("No path has been configured, check the plugin settings.")
			)
		try:
			bad_version = re.match(r"(?:0\.5\..+?)\Z", self.__get_arduino().version()["VersionString"]) is None
		except pyduinocli.ArduinoError:
			return dict(
				error=gettext("Invalid arduino-cli"),
				cause=gettext("The configured path does not point to an arduino-cli executable.")
			)
		except KeyError:
			bad_version = True
		if bad_version:
			return dict(
				error=gettext("Wrong arduino-cli version"),
				cause=gettext("The arduino-cli version you are using is not supported.")
			)
		return None

	def upload_file(self):
		self._firmware = None
		uploaded_file_path = flask.request.values["firmware_file." + self._settings.get_upload_path_suffix()]
		try:
			with zipfile.ZipFile(uploaded_file_path, "r") as zip_file:
				return self.__upload_zip(zip_file)
		except zipfile.BadZipfile:
			return self.__upload_hex(uploaded_file_path)

	def __upload_zip(self, zip_file):
		self.__is_ino = True
		firmware_dir = os.path.join(self._data_folder, "firmware")
		sketch_dir = os.path.join(firmware_dir, os.path.splitext(self._settings.get_arduino_sketch_ino())[0])
		if os.path.exists(firmware_dir):
			shutil.rmtree(firmware_dir)
		os.makedirs(sketch_dir)
		zip_file.extractall(sketch_dir)
		for root, dirs, files in os.walk(sketch_dir):
			for f in files:
				if f == self._settings.get_arduino_sketch_ino():
					self._firmware = root
					return dict(
						path=root,
						file=f
					), None
		return None, dict(
			error=gettext("No sketch found"),
			cause=gettext("No valid sketch were found in the given file.")
		)

	def __upload_hex(self, file_path):
		self.__is_ino = False
		self._firmware = os.path.join(self._data_folder, "firmware.hex")
		shutil.copyfile(file_path, self._firmware)
		return dict(
			path=self._data_folder,
			file="firmware.hex"
		), None
