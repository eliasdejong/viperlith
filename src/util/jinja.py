import os
from jinja2 import Environment, FileSystemLoader


templates = Environment(
	loader=FileSystemLoader("templates"),
	trim_blocks=True,
	lstrip_blocks=True,
	auto_reload=os.getenv("DEBUG") == "1",
	cache_size=400,
)