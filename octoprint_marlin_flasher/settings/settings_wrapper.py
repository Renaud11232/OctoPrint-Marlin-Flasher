class SettingsWrapper:

	def __init__(self, settings):
		self.__settings = settings

	def get_max_upload_size(self):
		return self.__settings.get_int(["max_upload_size"])

	def get_retrieving_method(self):
		return self.__settings.get(["retrieving_method"])

	def get_platform_type(self):
		return self.__settings.get(["platform_type"])

	def get_upload_path_suffix(self):
		return self.__settings.global_get(["server", "uploads", "pathSuffix"])

	def get_arduino_cli_path(self):
		return self.__settings.get(["arduino", "cli_path"])

	def get_arduino_additional_urls(self):
		return self.__settings.get(["arduino", "additional_urls"])

	def get_arduino_sketch_ino(self):
		return self.__settings.get(["arduino", "sketch_ino"])

	def get_platformio_cli_path(self):
		return self.__settings.get(["platformio", "cli_path"])

	def get_pre_flash_script(self):
		return self.__settings.get(["pre_flash_script"])

	def get_pre_flash_delay(self):
		return self.__settings.get(["pre_flash_delay"])

	def get_post_flash_script(self):
		return self.__settings.get(["post_flash_script"])

	def get_post_flash_delay(self):
		return self.__settings.get(["post_flash_delay"])

	def get_arduino_last_flash_options(self):
		return self.__settings.get(["arduino", "last_flash_options"])

	def get_platformio_last_flash_options(self):
		return self.__settings.get(["platformio", "last_flash_options"])

	def set_arduino_last_flash_options(self, value):
		return self.__settings.set(["arduino", "last_flash_options"], value)

	def set_platformio_last_flash_options(self, value):
		return self.__settings.set(["platformio", "last_flash_options"], value)

	def save(self, force=False, trigger_event=False):
		return self.__settings.save(force=force, trigger_event=trigger_event)
