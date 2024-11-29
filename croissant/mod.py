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
		self.all_scripts = []

		Mod.find_scripts(self)

	def find_scripts(self):
		for root, dirs, file in os.walk('mods'):
			for file in file:
				if file.endswith(".py"):
					self.all_scripts.append(file)
				if file == "main.py":
					exec(open(f"mods/{self.folder}/{file}").read())