import flask
from marshmallow import Schema, fields
from .base_validator import BaseValidator
from .validators import platformio


class PlatformIOValidator(BaseValidator):

	def validate_upload(self):
		request_fields = {
			"firmware_file." + self._settings.get_upload_path_suffix(): fields.Str(required=True, validate=platformio.is_correct_file_type)
		}
		return type("_PlatformIOUploadSchema", (Schema,), request_fields)().validate(flask.request.values)

	def validate_firmware(self):
		return Schema().validate(flask.request.values)

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
		return Schema().validate(flask.request.values)

	def validate_flash(self):
		request_fields = {
			"env": fields.Str(required=False)
		}
		return type("_PlatformIOFlashSchema", (Schema,), request_fields)().validate(flask.request.values)

	def validate_last_flash_options(self):
		return Schema().validate(flask.request.values)
