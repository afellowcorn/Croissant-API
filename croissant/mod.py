import os

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

	def call_ready(self):
		for _, _, file in os.walk('mods'):
			for file in file:
				if file == "main.py":
					try:
						exec(open(f"mods/{self.folder}/{file}").read())
					except:
						print(f"\033[1m[Croissant]\033[0m ERROR: {self.folder} main.py cannot be executed")