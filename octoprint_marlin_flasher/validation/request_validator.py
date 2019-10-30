from ..flasher.platform_type import PlatformType
from .platformio_validator import PlatformIOValidator
from .arduino_validator import ArduinoValidator
from .unsupported_validator import UnsupportedPlatformValidator


class RequestValidator:

	def __init__(self, settings, printer):
		self.__settings = settings
		self.__printer = printer
		self.__arduino_validator = ArduinoValidator(settings, printer)
		self.__platformio_validator = PlatformIOValidator(settings, printer)
		self.__unsupported_validator = UnsupportedPlatformValidator(settings, printer)

	def __get_implementation(self):
		platform = self.__settings.get_platform_type()
		if platform == PlatformType.ARDUINO:
			return self.__arduino_validator
		elif platform == PlatformType.PLATFORM_IO:
			return self.__platformio_validator
		else:
			return self.__unsupported_validator

	def validate_upload(self):
		return self.__get_implementation().validate_upload()

	def validate_core_search(self):
		return self.__get_implementation().validate_core_search()

	def validate_lib_search(self):
		return self.__get_implementation().validate_lib_search()

	def validate_core_install(self):
		return self.__get_implementation().validate_core_install()

	def validate_lib_install(self):
		return self.__get_implementation().validate_lib_install()

	def validate_core_uninstall(self):
		return self.__get_implementation().validate_core_uninstall()

	def validate_lib_uninstall(self):
		return self.__get_implementation().validate_lib_uninstall()

	def validate_board_listall(self):
		return self.__get_implementation().validate_board_listall()

	def validate_board_details(self):
		return self.__get_implementation().validate_board_details()

	def validate_flash(self):
		return self.__get_implementation().validate_flash()
