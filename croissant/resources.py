import ujson
from pathlib import Path
from collections.abc import Mapping

def open(path, *args, skip=False, **kwargs):
	cr_path = Path("croissant\\runtime_resources\\"+str(path))
	if not skip and cr_path.exists():
		return __builtins__["open"](cr_path, *args, **kwargs)
	return __builtins__["open"](path, *args, **kwargs)

def _load_resources(resources, folder) -> dict:
	"""Loads mod resources."""
	for path in Path(f"mods/{folder}").glob("**/*[!mod_info].json"):
		og_path = str(path).replace(f"mods\\{folder}\\", "")
		resources = _parse_json(resources, path, og_path)
	return resources

def _save_resources(resources) -> None:
	for key in resources.keys():
		path = Path("croissant\\runtime_resources\\"+str(key))
		path.parent.mkdir(exist_ok=True, parents=True)

		with open(path, 'w', skip=True) as file:
			data = ujson.dumps(resources[key], indent=4)
			file.write(data)

def _parse_json(resources, path, og_path) -> dict:
	if og_path in resources:
		og_data = resources[og_path]
	else:
		with open(og_path, 'r', skip=True) as read_file:
			og_data = ujson.loads(read_file.read())

	with open(path, 'r', skip=True) as read_file:
		data = ujson.loads(read_file.read())
	
	for segment in data:
		match segment["mode"]:
			case "append":
				og_data = _append(og_data, segment)
			case "update":
				og_data = _update(og_data, segment)

	resources[og_path] = og_data
	return resources

def _append(og_data, segment) -> dict:
	if isinstance(og_data, dict) and isinstance(segment["text"], dict):
		og_data = _append_dictionary(og_data, segment["text"])
	return og_data

def _append_dictionary(og_data, segment) -> dict:
	for key, value in segment.items():
		data_value = og_data.get(key)
		if isinstance(value, Mapping) and isinstance(data_value, Mapping):
			_append_dictionary(data_value, value)
		else:
			og_data[key] = value
	return og_data

def _update(og_data, segment) -> dict:
	og_data.update(segment["text"])
	return og_data