from .base_flasher import BaseFlasher


class ArduinoFlasher(BaseFlasher):

	def __init__(self, settings, printer):
		BaseFlasher.__init__(self, settings, printer)
		self.__is_ino = False

	def check_setup_errors(self):
		print("No errors")
		return None

	def upload_file(self):
		print("uploading file")
		return dict(
			path="le path",
			file="le file"
		), None
