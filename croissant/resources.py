import ujson
from pathlib import Path

def _load_resources(folder) -> None:
	"""Loads mod resources."""
	for path in Path(f"mods/{folder}").glob("**/*[!mod_info].json"):
		print(path)