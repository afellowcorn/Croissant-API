import ujson
from pathlib import Path
from collections.abc import Mapping


def open(path, *args, skip=False, **kwargs):
    cr_path = get_cr_path(path)
    if not skip and cr_path.exists():
        return __builtins__["open"](cr_path, *args, **kwargs)
    return __builtins__["open"](path, *args, **kwargs)


def get_cr_path(path) -> Path:
    """Return equivalent croissant resource path."""
    for x in ("resources\\", "resources/"):
    	# This is inconsistent, so both need to be removed
    	path = str(path).replace(x, "")
    return Path("croissant\\resources\\" + path)


def _load_resources(resources, folder) -> dict:
    """Loads mod resources."""
    for path in Path(f"mods/{folder}").glob("**/*[!mod_info].json"):
        og_path = str(path).replace(f"mods\\{folder}\\", "")
        resources = _parse_json(resources, path, og_path)
    return resources


def _save_resources(resources) -> None:
    """Saves mod resources."""
    for key in resources.keys():
        cr_path = get_cr_path(key)
        cr_path.parent.mkdir(exist_ok=True, parents=True)

        with open(cr_path, "w", skip=True) as file:
            data = ujson.dumps(resources[key], indent=4)
            file.write(data)


def _parse_json(resources, path, og_path):
    """Parses mod resource jsons and compiles them into one dict/list."""
    if og_path in resources:
        og_data = resources[og_path]
    else:
        with open(og_path, "r", skip=True) as read_file:
            og_data = ujson.loads(read_file.read())

    with open(path, "r", skip=True) as read_file:
        data = ujson.loads(read_file.read())

    for segment in data:
        match segment["mode"]:
            case "append":
                og_data = _append(og_data, segment)
            case "insert":
                og_data = _insert(og_data, segment)
            case "update":
                og_data = _update(og_data, segment)

    resources[og_path] = og_data
    return resources


def _append(og_data, segment):
    """Adds keys or list values to end of original, regardless of if the key or value exists already."""
    if isinstance(og_data, dict) and isinstance(segment["text"], dict):
        og_data = _append_dictionary(og_data, segment["text"])
    else:
        og_data.append(segment["text"])
    return og_data


def _append_dictionary(og_data, segment) -> dict:
    """Appends dictionary keys to original dictionary."""
    for key, value in segment.items():
        data_value = og_data.get(key)
        if isinstance(value, Mapping) and isinstance(data_value, Mapping):
            _append_dictionary(data_value, value)
        else:
            og_data[key] = value
    return og_data

def _insert(og_data, segment):
	"""Inserts segment at index for list or after specified key for dict."""
	if isinstance(og_data, dict):
		og_data = _insert_dictionary(og_data, segment)
	else:
		og_data.insert(int(segment["insert_at"]), segment["text"])
	return og_data

def _insert_dictionary(og_data, segment) -> dict:
	"""Inserts segment after a specified key in the original dictionary."""
	new_dict = {}
	for key, value in og_data.items():
		if isinstance(value, dict):
			value = _insert_dictionary(value, segment)
		new_dict.update({key: value})
		if key == segment["insert_at"]:
			new_dict.update(segment["text"])
	return new_dict

def _update(og_data, segment) -> dict:
    """Replaces key in original if it exists, and adds it if it doesn't."""
    og_data.update(segment["text"])
    return og_data
