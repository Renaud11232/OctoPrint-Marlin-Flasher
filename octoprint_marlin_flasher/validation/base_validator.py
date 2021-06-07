import flask
from flask_babel import gettext


class BaseValidator:

	def __init__(self, settings):
		self._settings = settings

	def validate_upload(self):
		errors = []
		if "firmware_file." + self._settings.get_upload_path_suffix() not in flask.request.values:
			errors.append(gettext("Uploaded file is missing"))
		return errors

	def validate_download(self):
		errors = []
		if "url" not in flask.request.values:
			errors.append(gettext("The url field is missing"))
		return errors
