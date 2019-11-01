from .base_flasher import BaseFlasher
from .flasher_error import FlasherError
from subprocess import Popen, PIPE
import zipfile
import os
import shutil
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
			bad_exec = "platformio" in self.__exec(["--version"])
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
		# TODO not done yet
		return None, None
