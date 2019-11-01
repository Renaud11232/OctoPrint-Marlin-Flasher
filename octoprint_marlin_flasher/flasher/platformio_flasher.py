from .base_flasher import BaseFlasher
import zipfile
import os
import shutil
import flask
from flask_babel import gettext


class PlatformIOFlasher(BaseFlasher):

	def check_setup_errors(self):
		return dict(
			# TODO not done yet
			error=gettext("check_setup_errors: not implemented yet")
		)

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
		return BaseFlasher.flash(self)
