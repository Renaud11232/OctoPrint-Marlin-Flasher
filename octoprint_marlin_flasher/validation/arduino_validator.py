import flask
from marshmallow import Schema, fields
from .base_validator import BaseValidator
from .validators import arduino


class ArduinoValidator(BaseValidator):

	def validate_upload(self):
		request_fields = {
			"firmware_file." + self._settings.get_upload_path_suffix(): fields.Str(required=True, validate=arduino.is_correct_file_type)
		}
		return type("_ArduinoUploadSchema", (Schema,), request_fields)().validate(flask.request.values)

	def validate_core_search(self):
		request_fields = {
			"query": fields.Str(required=False)
		}
		return type("_ArduinoCoreSearchSchema", (Schema,), request_fields)().validate(flask.request.values)

	def validate_lib_search(self):
		request_fields = {
			"query": fields.Str(required=False)
		}
		return type("_ArduinoLibSearchSchema", (Schema,), request_fields)().validate(flask.request.values)

	def validate_core_install(self):
		request_fields = {
			"core": fields.Str(required=True)
		}
		return type("_ArduinoCoreInstallSchema", (Schema,), request_fields)().validate(flask.request.values)

	def validate_lib_install(self):
		request_fields = {
			"lib": fields.Str(required=True)
		}
		return type("_ArduinoLibInstallSchema", (Schema,), request_fields)().validate(flask.request.values)

	def validate_core_uninstall(self):
		request_fields = {
			"core": fields.Str(required=True)
		}
		return type("_ArduinoCoreUninstallSchema", (Schema,), request_fields)().validate(flask.request.values)

	def validate_lib_uninstall(self):
		request_fields = {
			"lib": fields.Str(required=True)
		}
		return type("_ArduinoLibUninstallSchema", (Schema,), request_fields)().validate(flask.request.values)

	def validate_board_listall(self):
		return None

	def validate_board_details(self):
		request_fields = {
			"fqbn": fields.Str(required=True)
		}
		return type("_ArduinoBoardDetailsSchema", (Schema,), request_fields)().validate(flask.request.values)

	def validate_flash(self):
		request_fields = {
			"fqbn": fields.Str(required=True)
		}
		return type("_ArduinoFlashSchema", (Schema,), request_fields)().validate(flask.request.values)
