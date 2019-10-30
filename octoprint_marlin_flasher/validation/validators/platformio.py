from flask_babel import gettext
from marshmallow import ValidationError, Schema
import zipfile


class PlatformIOUnsupportedSchema(Schema):

	def validate(self, _):
		return dict(
			error=gettext("Unsupported endpoint."),
			cause=gettext("You tried to run a command that is not supported by this platform.")
		)


def is_correct_file_type(filename):
	try:
		with zipfile.ZipFile(filename, "r") as _:
			pass
	except zipfile.BadZipfile:
		raise ValidationError(gettext("Invalid file type."))
