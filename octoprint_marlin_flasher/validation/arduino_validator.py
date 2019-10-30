import flask
from marshmallow import Schema, fields
from .base_validator import BaseValidator
from .schema import arduino


class ArduinoValidator(BaseValidator):

	def validate_upload(self):
		request_fields = {
			"firmware_file." + self._settings.global_get(["server", "uploads", "pathSuffix"]): fields.Str(required=True, validate=arduino.is_correct_file_type),

		}
		return type("_ArduinoUploadSchema", (Schema,), request_fields)().validate(flask.request.values)
