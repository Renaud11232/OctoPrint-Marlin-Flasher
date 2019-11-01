from .base_flasher import BaseFlasher
from flask_babel import gettext


class UnsupportedFlasher(BaseFlasher):

	def check_setup_errors(self):
		return dict(
			error=gettext("Unkown platform, please check your settings.")
		)
