import flask
from .base_validator import BaseValidator
from flask_babel import gettext


class PlatformIOValidator(BaseValidator):

	def validate_flash(self):
		errors = []
		if "env" not in flask.request.values:
			errors.append(gettext("The env field is missing"))
		return errors
