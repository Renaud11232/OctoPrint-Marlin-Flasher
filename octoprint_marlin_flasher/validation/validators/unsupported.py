from flask_babel import gettext
from marshmallow import Schema


class UnsupportedSchema(Schema):

	def validate(self, _):
		return dict(
			error=gettext("Unknown platform type."),
			cause=gettext("Your configuration might be wrong, check the settings page")
		)
