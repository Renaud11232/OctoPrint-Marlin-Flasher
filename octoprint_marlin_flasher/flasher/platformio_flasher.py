from .base_flasher import BaseFlasher
from .flasher_error import FlasherError
from subprocess import Popen, PIPE
import zipfile
import os
import shutil
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
			firmware_dir = os.path.join(self._plugin.get_plugin_data_folder(), "firmware")
			if os.path.exists(firmware_dir):
				shutil.rmtree(firmware_dir)
			os.makedirs(firmware_dir)
			zip_file.extractall(firmware_dir)
			for root, dirs, files in os.walk(firmware_dir):
				for f in files:
					if f == "platformio.ini":
						self._firmware = root
						return dict(
							path=root,
							file=f
						), None
			return None, dict(
				error=gettext("No Platform.io configuration file were found in the given file.")
			)

	def flash(self):
		if self._firmware is None:
			return None, dict(
				error=gettext("You did not upload the firmware or it got reset by the previous flash process.")
			)
		if not self._printer.is_ready():
			return None, dict(
				error=gettext("The printer may not be connected or it may be busy.")
			)
		try:
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="flash_progress",
				step=gettext("Compiling"),
				progress=0
			))
			self.__exec(["run", "-d", self._firmware])
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="flash_progress",
				step=gettext("Uploading"),
				progress=50
			))
			transport = self._printer.get_transport()
			if not isinstance(transport, serial.Serial):
				return None, dict(
					error=gettext("The printer is not connected through a Serial port and thus, cannot be flashed.")
				)
			flash_port = transport.port
			_, port, baudrate, profile = self._printer.get_current_connection()
			self._printer.disconnect()
			self.__exec(["run", "-d", self._firmware, "-t", "upload", "--upload-port", flash_port])
			self._printer.connect(port, baudrate, profile)
			self._firmware = None
			self._plugin_manager.send_plugin_message(self._identifier, dict(
				type="flash_progress",
				step=gettext("Done"),
				progress=100
			))
			return dict(
				message=gettext("Board successfully flashed.")
			), None
		except FlasherError as e:
			return None, dict(
				error=gettext("The flashing process failed"),
				stderr=e.message
			)
