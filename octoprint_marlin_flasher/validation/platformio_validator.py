import flask
from marshmallow import Schema, fields
from .base_validator import BaseValidator
from flask_babel import gettext


class PlatformIOUnsupportedSchema(Schema):

	def validate(self, _):
		return dict(
			error=gettext("This endpoint is not supported by the current platform.")
		)


class PlatformIOValidator(BaseValidator):

	def validate_upload(self):
		errors = []
		if "firmware_file." + self._settings.get_upload_path_suffix() not in flask.request.values:
			errors.append("Uploaded file is missing")
		return errors

	def validate_download(self):
		request_fields = {
			"url": fields.Url(required=True)
		}
		return type("_PlatformIODownloadSchema", (Schema,), request_fields)().validate(flask.request.values)

	def validate_firmware(self):
		return Schema().validate(flask.request.values)

	def validate_core_search(self):
		return PlatformIOUnsupportedSchema().validate(flask.request.values)

	def validate_lib_search(self):
		return PlatformIOUnsupportedSchema().validate(flask.request.values)

	def validate_core_install(self):
		return PlatformIOUnsupportedSchema().validate(flask.request.values)

	def validate_lib_install(self):
		return PlatformIOUnsupportedSchema().validate(flask.request.values)

	def validate_core_uninstall(self):
		return PlatformIOUnsupportedSchema().validate(flask.request.values)

	def validate_lib_uninstall(self):
		return PlatformIOUnsupportedSchema().validate(flask.request.values)

	def validate_board_listall(self):
		return PlatformIOUnsupportedSchema().validate(flask.request.values)

	def validate_board_details(self):
		return Schema().validate(flask.request.values)

	def validate_flash(self):
		request_fields = {
			"env": fields.Str(required=False)
		}
		return type("_PlatformIOFlashSchema", (Schema,), request_fields)().validate(flask.request.values)

	def validate_last_flash_options(self):
		return Schema().validate(flask.request.values)
