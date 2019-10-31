from flask_babel import gettext
from marshmallow import Schema


class UnsupportedSchema(Schema):

	def validate(self, _):
		return dict(
			error=gettext("The configured platform is not supported. Check your settings")
		)
