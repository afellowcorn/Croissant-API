import ujson
from pathlib import Path

def _load_resources(folder) -> None:
	"""Loads mod resources."""
	for file in Path(f"mods/{folder}").glob("**/*.json"):
		print(file)