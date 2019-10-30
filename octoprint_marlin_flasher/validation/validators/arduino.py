from flask_babel import gettext
from marshmallow import ValidationError
import intelhex
import zipfile


def is_correct_file_type(filename):
	try:
		with zipfile.ZipFile(filename, "r") as _:
			pass
	except zipfile.BadZipfile:
		try:
			ih = intelhex.IntelHex()
			ih.loadhex(filename)
		except intelhex.IntelHexError:
			raise ValidationError(gettext("Invalid file type."))
