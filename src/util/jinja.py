import os
from jinja2 import Environment, FileSystemLoader
# from litestar.plugins.jinja import JinjaTemplateEngines
# from litestar.template.config import TemplateConfig


templates = Environment(
	loader=FileSystemLoader("templates"),
	trim_blocks=True,
	lstrip_blocks=True,
	auto_reload=os.getenv("DEBUG") != "0",
	cache_size=400,
)

# template_config = TemplateConfig(
# 	engine=JinjaTemplateEngine.from_environment(templates),
# )