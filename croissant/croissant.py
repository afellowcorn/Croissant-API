import os
import sys

import functools
import inspect
import ujson
from importlib.abc import MetaPathFinder, Loader
from importlib.util import spec_from_file_location, module_from_spec
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from croissant.mod import Mod
#from croissant import patcher

T = TypeVar('T')

class Croissant:
	mod_list: Dict[str, Mod] = {}
	_patches: Dict[str, Dict[str, List[Callable]]] = {
		'prefix': {},
		'postfix': {},
		'replace': {}
	}
	_patched_modules = set()

	print(f"\033[1m[Croissant]\033[0m Initialized")

	@classmethod
	def load_mods(cls) -> None:
		"""Creates a Mod class instance for every mod folder."""

		for folder in (next(os.walk('mods'))[1]):
			mod_info = None
			if folder == "template":
				continue

			try:
				with open(f"mods/{folder}/mod_info.json", 'r') as read_file:
					mod_info = ujson.loads(read_file.read())
				Croissant.mod_list.update({mod_info["mod_id"]: Mod(folder, mod_info)})

				Croissant.mod_list[mod_info["mod_id"]].call_ready()

			except:
				print(f"\033[1m[Croissant]\033[0m ERROR: {folder} does not have a mod_info.json")

		print(f"\033[1m[Croissant]\033[0m Mod loading complete")

	@classmethod
	def _get_full_name(cls, func: Callable) -> str:
		"""Get the full name of a function including module."""
		if inspect.ismethod(func):
			# Handle bound methods
			if hasattr(func, '__self__'):
				if inspect.isclass(func.__self__):
					# Class method
					return f"{func.__module__}.{func.__self__.__name__}.{func.__name__}"
				else:
					# Instance method
					return f"{func.__module__}.{func.__self__.__class__.__name__}.{func.__name__}"
		elif inspect.isfunction(func):
			# Handle unbound methods and functions
			if '.' in func.__qualname__:
				# This is likely a method defined in a class
				return f"{func.__module__}.{func.__qualname__}"
			else:
				# This is a regular function
				return f"{func.__module__}.{func.__name__}"
		return f"{func.__module__}.{func.__qualname__}"

	@classmethod
	def _wrap_function(cls, func: Callable[..., T], owner_class=None) -> Callable[..., T]:
		"""Create a wrapper that applies all patches."""
		is_classmethod = isinstance(func, classmethod) or (owner_class and isinstance(getattr(owner_class, func.__name__, None), classmethod))
		is_staticmethod = isinstance(func, staticmethod) or (owner_class and isinstance(getattr(owner_class, func.__name__, None), staticmethod))
		
		# Get the actual function from classmethod/staticmethod if needed
		if isinstance(func, (classmethod, staticmethod)):
			func = func.__get__(None, owner_class).__func__
		
		full_name = cls._get_full_name(func)
		
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			# Prepare arguments
			if is_classmethod:
				patch_args = (args[0],) + args[1:] if args else (owner_class,)
			else:
				patch_args = args
			
			# Prefix
			for prefix_patch in cls._patches['prefix'].get(full_name, []):
				prefix_patch(*patch_args, **kwargs)
			
			# Replace
			if full_name in cls._patches['replace'] and cls._patches['replace'][full_name]:
				result = cls._patches['replace'][full_name][-1](*patch_args, **kwargs)
			else:
				result = func(*args, **kwargs)
			
			# Postfix
			for postfix_patch in cls._patches['postfix'].get(full_name, []):
				postfix_patch(*patch_args, **kwargs)
			
			return result
		
		# Preserve method type
		if is_classmethod:
			return classmethod(wrapper)
		elif is_staticmethod:
			return staticmethod(wrapper)
		
		return wrapper

	@classmethod
	def patch(cls, target: Union[str, Callable], patch_type: str = 'replace') -> Callable:
		"""
		Decorator to patch a function.
		
		Args:
			target: The function to patch or its full name
			patch_type: One of 'prefix', 'postfix', or 'replace'
		"""
		def decorator(patch_func: Callable) -> Callable:
			if isinstance(target, str):
				target_name = target
			else:
				target_name = cls._get_full_name(target)
			
			if patch_type not in cls._patches:
				raise ValueError(f"Invalid patch type: {patch_type}")
			
			if target_name not in cls._patches[patch_type]:
				cls._patches[patch_type][target_name] = []
			
			cls._patches[patch_type][target_name].append(patch_func)
			
			# Try to patch any already loaded modules that might contain this target
			cls.patch_loaded_modules()
			return patch_func
		
		return decorator

	@classmethod
	def _patch_module(cls, module) -> None:
		"""Apply patches to a single module."""
		# if module is None or module.__name__ in cls._patched_modules:
		# 	return
			
		for attr_name in dir(module):
			try:
				attr = getattr(module, attr_name)
				if inspect.isclass(attr):
					# Patch class methods
					for method_name, method in inspect.getmembers(attr, predicate=lambda x: inspect.isfunction(x) or inspect.ismethod(x) or isinstance(x, (classmethod, staticmethod))):
						full_name = f"{module.__name__}.{attr.__name__}.{method_name}"
						has_patches = any(
							full_name in patch_dict
							for patch_dict in cls._patches.values()
						)
						if has_patches:
							wrapped = cls._wrap_function(method, owner_class=attr)
							setattr(attr, method_name, wrapped)
				elif callable(attr):
					# Patch regular functions
					full_name = cls._get_full_name(attr)
					has_patches = any(
						full_name in patch_dict
						for patch_dict in cls._patches.values()
					)
					if has_patches:
						wrapped = cls._wrap_function(attr)
						setattr(module, attr_name, wrapped)
			except (AttributeError, TypeError):
				continue
		
		cls._patched_modules.add(module.__name__)
	
	@classmethod
	def patch_loaded_modules(cls) -> None:
		"""
		Patch all currently loaded modules in sys.modules.
		This allows patching modules that were imported before the patch was defined.
		"""
		for module_name, module in list(sys.modules.items()):
			cls._patch_module(module)
	
	@classmethod
	def patch_module(cls, module_name: str) -> None:
		"""
		Explicitly patch a specific module by name.
		"""
		if module_name in sys.modules:
			cls._patch_module(sys.modules[module_name])

class PatchFinder(MetaPathFinder):
	def find_spec(self, fullname, path, target=None):
		if path is None:
			path = sys.path
		
		for entry in path:
			if not isinstance(entry, str) or not os.path.isdir(entry):
				continue
				
			filename = os.path.join(entry, fullname.split('.')[-1] + '.py')
			if not os.path.exists(filename):
				continue
				
			return spec_from_file_location(
				fullname, 
				filename,
				loader=PatchLoader(filename)
			)
		return None

class PatchLoader(Loader):
	def __init__(self, filename):
		self.filename = filename
	
	def create_module(self, spec):
		return None  # Use default module creation
	
	def exec_module(self, module):
		with open(self.filename) as f:
			exec(f.read(), module.__dict__)
		Croissant._patch_module(module)

# Install the import hook
sys.meta_path.insert(0, PatchFinder())

	# mod_list: Dict[str, Mod] = {}
	# hook_list = []

	# print(f"\033[1m[Croissant]\033[0m Initialized")

	# @staticmethod
	# def load_mods():
	# 	"""Creates a Mod class instance for every folder and passes mod_info.json"""

	# 	for folder in (next(os.walk('mods'))[1]):

	# 		if folder == "template":
	# 			continue

	# 		mod_info = None
	# 		try:
	# 			with open(f"mods/{folder}/mod_info.json", 'r') as read_file:
	# 				mod_info = ujson.loads(read_file.read())
	# 			Croissant.mod_list.update({mod_info["mod_id"]: Mod(folder, mod_info)})

	# 			#Croissant.mod_list[mod_info["mod_id"]].call_ready()

	# 		except:
	# 			print(f"\033[1m[Croissant]\033[0m ERROR: {folder} does not have a mod_info.json")

	# 	print(f"\033[1m[Croissant]\033[0m Mod loading complete")


	# @staticmethod
	# def add_hook(target, function, prefix, callid):
	# 	"""
	# 	:param target: target Clangen function to be hooked to
	# 	:param function: hook function
	# 	:param prefix: if True hook is executed before target
	# 	:param callid: custom id string for own use or mod compatibilities

	# 	"""
	# 	hook = {
	# 		"target": target,
	# 		"function": function,
	# 		"prefix": prefix,
	# 		"callid": callid
	# 	}
	# 	Croissant.hook_list.append(hook)

	# @staticmethod
	# def call_catcher(frame, event, arg):
	# 	# If a hook targeting current frame exists calls patch() and passes arguments

	# 	for hook in Croissant.hook_list:
	# 		if hook["target"].__name__ == frame.f_code.co_name:
	# 			args, _, _, values = getargvalues(frame)
	# 			args = (tuple(values[i] for i in args))
	# 			Croissant.patch(hook["target"], hook, *args)
	# 	return None

	# @staticmethod
	# def patch(orig, hook, *args, **kwargs):
	# 	if hook["prefix"]:
	# 		orig = (Croissant.hook_prefix(orig, hook["function"], *args, **kwargs))(*args, **kwargs)
	# 	else:
	# 		orig = (Croissant.hook_postfix(orig, hook["function"], *args, **kwargs))(*args, **kwargs)

	# @staticmethod
	# def hook_prefix(orig, hook, *args, **kwargs):
	# 	def run(*args, **kwargs):
	# 		hook(*args, **kwargs)
	# 		return orig(*args, **kwargs)
	# 	return run

	# @staticmethod
	# def hook_postfix(orig, hook, *args, **kwargs):
	# 	def run(*args, **kwargs):
	# 		orig(*args, **kwargs)
	# 		return hook(*args, **kwargs)
	# 	return run