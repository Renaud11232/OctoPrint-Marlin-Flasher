import flask
from flask_babel import gettext
from .base_validator import BaseValidator


class ArduinoValidator(BaseValidator):

	def validate_core_search(self):
		errors = []
		if "query" not in flask.request.values:
			errors.append(gettext("The query field is missing"))
		return errors

	def validate_lib_search(self):
		errors = []
		if "query" not in flask.request.values:
			errors.append(gettext("The query field is missing"))
		return errors

	def validate_core_install(self):
		errors = []
		if "core" not in flask.request.values:
			errors.append(gettext("The core field is missing"))
		return errors

	def validate_lib_install(self):
		errors = []
		if "lib" not in flask.request.values:
			errors.append(gettext("The lib field is missing"))
		return errors

	def validate_core_uninstall(self):
		errors = []
		if "core" not in flask.request.values:
			errors.append(gettext("The core field is missing"))
		return errors

	def validate_lib_uninstall(self):
		errors = []
		if "lib" not in flask.request.values:
			errors.append(gettext("The lib field is missing"))
		return errors

	def validate_board_details(self):
		errors = []
		if "fqbn" not in flask.request.values:
			errors.append(gettext("The fqbn field is missing"))
		return errors

	def validate_flash(self):
		errors = []
		if "fqbn" not in flask.request.values:
			errors.append(gettext("The fqbn field is missing"))
		return errors
