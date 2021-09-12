import flask
from .base_validator import BaseValidator
from flask_babel import gettext


class PlatformIOValidator(BaseValidator):

	def validate_flash(self):
		errors = []
		if "env" not in flask.request.values:
			errors.append(gettext("The env field is missing"))
		return errors

	def validate_login(self):
		errors = []
		if "username" not in flask.request.values:
			errors.append(gettext("The username is missing"))
		if "password" not in flask.request.values:
			errors.append(gettext("The password is missing"))
		return errors

	def validate_logout(self):
		return []

	def validate_start_remote_agent(self):
		return []

	def validate_stop_remote_agent(self):
		return []
