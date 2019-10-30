import flask
from marshmallow import Schema, fields
from .base_validator import BaseValidator
from .validators import arduino


class ArduinoValidator(BaseValidator):

	def validate_upload(self):
		request_fields = {
			"firmwaare_file." + self._settings.global_get(["server", "uploads", "pathSuffix"]): fields.Str(required=True, validate=arduino.is_correct_file_type),

		}
		return type("_ArduinoUploadSchema", (Schema,), request_fields)().validate(flask.request.values)

	def validate_core_search(self):
		request_fields = {
			"query": fields.Str(required=False)
		}
		return type("_ArduinoCoreSearchSchema", (arduino.ArduinoSchema,), request_fields)(self._settings).validate(flask.request.values)

	def validate_lib_search(self):
		request_fields = {
			"query": fields.Str(required=False)
		}
		return type("_ArduinoLibSearchSchema", (arduino.ArduinoSchema,), request_fields)(self._settings).validate(flask.request.values)

	def validate_core_install(self):
		request_fields = {
			"core": fields.Str(required=False)
		}
		return type("_ArduinoCoreInstallSchema", (arduino.ArduinoSchema,), request_fields)(self._settings).validate(flask.request.values)

	def validate_lib_install(self):
		request_fields = {
			"lib": fields.Str(required=False)
		}
		return type("_ArduinoLibInstallSchema", (arduino.ArduinoSchema,), request_fields)(self._settings).validate(flask.request.values)

	def validate_core_uninstall(self):
		request_fields = {
			"core": fields.Str(required=False)
		}
		return type("_ArduinoCoreUninstallSchema", (arduino.ArduinoSchema,), request_fields)(self._settings).validate(flask.request.values)

	def validate_lib_uninstall(self):
		request_fields = {
			"lib": fields.Str(required=False)
		}
		return type("_ArduinoLibUninstallSchema", (arduino.ArduinoSchema,), request_fields)(self._settings).validate(flask.request.values)

	def validate_board_listall(self):
		return type("_ArduinoBoardListalllSchema", (arduino.ArduinoSchema,), {})(self._settings).validate(flask.request.values)

	def validate_board_details(self):
		request_fields = {
			"fqbn": fields.Str(required=False)
		}
		return type("_ArduinoBoardDetailsSchema", (arduino.ArduinoSchema,), request_fields)(self._settings).validate(flask.request.values)

	def validate_flash(self):
		request_fields = {
			"fqbn": fields.Str(required=False)
		}
		return type("_ArduinoFlashSchema", (arduino.ArduinoSchema,), request_fields)(self._settings).validate(flask.request.values)
