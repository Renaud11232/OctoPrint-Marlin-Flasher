from flask_babel import gettext
from marshmallow import ValidationError, Schema
import zipfile


class PlatformIOUnsupportedSchema(Schema):

	def validate(self, _):
		return dict(
			error=gettext("This endpoint is not supported by the active firmware platform")
		)


def is_correct_file_type(filename):
	try:
		with zipfile.ZipFile(filename, "r") as _:
			pass
	except zipfile.BadZipfile:
		raise ValidationError(gettext("Invalid file type"))
