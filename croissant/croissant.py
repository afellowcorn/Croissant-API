import os
import sys

import ujson
from inspect import getargvalues

from croissant.mod import Mod


class Croissant:
	mod_list = []
	mod_id_list = []
	hook_list = []

	print(f"\033[1m[Croissant]\033[0m Initialized")

	@staticmethod
	def load_mods():
		# Creates a Mod class instance for every folder and passes mod_info.json
		for folder in (next(os.walk('mods'))[1]):
			mod_info = None
			try:
				with open(f"mods/{folder}/mod_info.json", 'r') as read_file:
					mod_info = ujson.loads(read_file.read())
				Croissant.mod_list.append(Mod(folder, mod_info))
			except:
				print(f"\033[1m[Croissant]\033[0m ERROR: {folder} does not have a mod_info.json")
		print(f"\033[1m[Croissant]\033[0m Mod loading complete")

	@staticmethod
	def add_hook(target, function, prefix, callid):
		"""
		:param target: target Clangen function to be hooked to
		:param function: hook function
		:param prefix: if True hook is executed before target
		:param callid: custom id string for own use or mod compatibilities

		"""
		hook = {
			"target": target,
			"function": function,
			"prefix": prefix,
			"callid": callid
		}
		Croissant.hook_list.append(hook)

	@staticmethod
	def call_catcher(frame, event, arg):
		for hook in Croissant.hook_list:
			if hook["target"].__name__ == frame.f_code.co_name:
				args, _, _, values = getargvalues(frame)
				args = (tuple(values[i] for i in args))
				Croissant.patch(hook["target"], hook["function"], *args)
		return None

	@staticmethod
	def patch(orig, hook, *args, **kwargs):
		orig = (Croissant.hook_prefix(orig, hook, *args, **kwargs))(*args, **kwargs)

	@staticmethod
	def hook_prefix(orig, hook, *args, **kwargs):
		def run(*args, **kwargs):
			hook(*args, **kwargs)
			return orig(*args, **kwargs)
		return run

	@staticmethod
	def hook_postfix(orig, hook, *args, **kwargs):
		def run(*args, **kwargs):
			orig(*args, **kwargs)
			return hook(*args, **kwargs)
		return run
