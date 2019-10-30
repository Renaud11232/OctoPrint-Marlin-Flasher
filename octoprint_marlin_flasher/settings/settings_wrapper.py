class SettingsWrapper:

	def __init__(self, settings):
		self.__settings = settings

	def get_max_upload_size(self):
		return self.__settings.get_int(["max_upload_size"])

	def get_platform_type(self):
		return self.__settings.get_int(["platform_type"])

	def get_upload_path_suffix(self):
		return self.__settings.global_get(["server", "uploads", "pathSuffix"])
