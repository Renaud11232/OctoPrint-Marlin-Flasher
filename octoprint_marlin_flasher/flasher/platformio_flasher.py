from .base_flasher import BaseFlasher
from flask_babel import gettext


class PlatformIOFlasher(BaseFlasher):

	def check_setup_errors(self):
		return dict(
			# TODO not done yet
			error=gettext("Not implemented yet")
		)
