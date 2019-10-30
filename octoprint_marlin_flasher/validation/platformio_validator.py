import flask
from marshmallow import Schema, fields
from .base_validator import BaseValidator
from .validators import platformio


class PlatformIOValidator(BaseValidator):

	def validate_upload(self):
		request_fields = {
			"firmware_file." + self._settings.global_get(["server", "uploads", "pathSuffix"]): fields.Str(required=True, validate=platformio.is_correct_file_type)
		}
		return type("_PlatformIOUploadSchema", (Schema,), request_fields)().validate(flask.request.values)

	def validate_core_search(self):
		return platformio.PlatformIOUnsupportedSchema().validate(flask.request.values)

	def validate_lib_search(self):
		return platformio.PlatformIOUnsupportedSchema().validate(flask.request.values)

	def validate_core_install(self):
		return platformio.PlatformIOUnsupportedSchema().validate(flask.request.values)

	def validate_lib_install(self):
		return platformio.PlatformIOUnsupportedSchema().validate(flask.request.values)

	def validate_core_uninstall(self):
		return platformio.PlatformIOUnsupportedSchema().validate(flask.request.values)

	def validate_lib_uninstall(self):
		return platformio.PlatformIOUnsupportedSchema().validate(flask.request.values)

	def validate_board_listall(self):
		return platformio.PlatformIOUnsupportedSchema().validate(flask.request.values)

	def validate_board_details(self):
		return platformio.PlatformIOUnsupportedSchema().validate(flask.request.values)

	# TODO needs to be actually done when adding platformio support
	def validate_flash(self):
		return platformio.PlatformIOUnsupportedSchema().validate(flask.request.values)
