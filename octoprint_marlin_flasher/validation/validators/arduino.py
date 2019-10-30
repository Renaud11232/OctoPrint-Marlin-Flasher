import re
from flask_babel import gettext
from marshmallow import ValidationError, Schema
import pyduinocli
import intelhex
import zipfile


class ArduinoSchema(Schema):

	def __init__(self, settings):
		Schema.__init__(self)
		self._settings = settings

	def validate(self, data):
		if is_bad_arduino_version(self._settings):
			return dict(
				message=gettext("You are not using a supported arduino-cli version, check the settings page.")
			)
		return Schema.validate(self, data)


def is_bad_arduino_version(settings):
	arduino_path = settings.get(["arduino", "cli_path"])
	no_arduino_path = arduino_path is None
	bad_arduino = False
	if not no_arduino_path:
		try:
			bad_arduino = re.match(r"(?:0\.5\..+?)\Z", pyduinocli.Arduino(arduino_path).version()["VersionString"]) is None
		except (pyduinocli.ArduinoError, KeyError):
			bad_arduino = True
	return no_arduino_path or bad_arduino


def is_correct_file_type(filename):
	try:
		with zipfile.ZipFile(filename, "r") as z:
			pass
	except zipfile.BadZipfile:
		try:
			ih = intelhex.IntelHex()
			ih.loadhex(filename)
		except intelhex.IntelHexError:
			raise ValidationError(gettext("Invalid file type"))
