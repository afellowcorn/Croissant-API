import ujson

def parser():
	with open(f"mods/{folder}/{file}", 'r') as read_file:
		settings = ujson.loads(read_file.read())