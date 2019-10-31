from .arduino_flasher import ArduinoFlasher
from .platformio_flasher import PlatformIOFlasher
from .unsupported_flasher import UnsupportedFlasher
from .platform_type import PlatformType


class MarlinFlasher:

	def __init__(self, settings, printer, plugin, plugin_manager, identifier):
		self.__firmware = None
		self.__settings = settings
		self.__arduino_flasher = ArduinoFlasher(settings, printer, plugin, plugin_manager, identifier)
		self.__platformio_flasher = PlatformIOFlasher(settings, printer, plugin, plugin_manager, identifier)
		self.__unsupported_flasher = UnsupportedFlasher(settings, printer, plugin, plugin_manager, identifier)

	def __get_implementation(self):
		platform = self.__settings.get_platform_type()
		if platform == PlatformType.ARDUINO:
			return self.__arduino_flasher
		elif platform == PlatformType.PLATFORM_IO:
			return self.__platformio_flasher
		else:
			return self.__unsupported_flasher

	@staticmethod
	def __run_after_check(impl, func):
		setup_errors = impl.check_setup_errors()
		if setup_errors:
			return None, setup_errors
		return func()

	def check_setup_errors(self):
		return self.__get_implementation().check_setup_errors()

	def upload_file(self):
		return self.__get_implementation().upload_file()

	def core_search(self):
		impl = self.__get_implementation()
		return self.__run_after_check(impl, impl.core_search)

	def lib_search(self):
		impl = self.__get_implementation()
		return self.__run_after_check(impl, impl.lib_search)

	def core_install(self):
		impl = self.__get_implementation()
		return self.__run_after_check(impl, impl.core_install)

	def lib_install(self):
		impl = self.__get_implementation()
		return self.__run_after_check(impl, impl.lib_install)

	def core_uninstall(self):
		impl = self.__get_implementation()
		return self.__run_after_check(impl, impl.core_uninstall)

	def lib_uninstall(self):
		impl = self.__get_implementation()
		return self.__run_after_check(impl, impl.lib_uninstall)

	def board_listall(self):
		impl = self.__get_implementation()
		return self.__run_after_check(impl, impl.board_listall)

	def board_details(self):
		impl = self.__get_implementation()
		return self.__run_after_check(impl, impl.board_details)

	def flash(self):
		impl = self.__get_implementation()
		return self.__run_after_check(impl, impl.flash)
