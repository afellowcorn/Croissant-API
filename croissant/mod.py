import os
import ujson

class Mod:
	def __init__(
        self,
        folder=None,
        mod_info={}
    ):
		self.folder = folder

		self.mod_id = mod_info["mod_id"]
		self.name = mod_info["name"]
		self.version = mod_info["version"]
		self.description = mod_info["description"]
		self.dependency_id = mod_info["dependency_id"]
		self.dependency_name = mod_info["dependency_name"]

		self.settings = {}

	def call_ready(self):
		for _, _, file in os.walk('mods'):
			for file in file:
				if file == "main.py":
					try:
						exec(open(f"mods/{self.folder}/{file}").read())
					except Exception as e:
						print(f"\033[1m[Croissant]\033[0m ERROR: {self.folder} main.py cannot be executed: \033[31m{e}\033[0m")

						return None
				elif file == "settings.json":
					with open(f"mods/{self.folder}/{file}", 'r') as read_file:
						self.settings = ujson.loads(read_file.read())
