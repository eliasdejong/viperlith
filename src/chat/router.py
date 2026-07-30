import os
import asyncio
from litestar import Router, get, post
from litestar.di import NamedDependency
from litestar.connection import Request
from litestar.response import Response, Stream

from src.util.jinja import templates
from src.util.db_write_con import con
from src.util.sse_generator import sse_generator


async def main_loop():
	async for _ in frame_ticks():
		pass


def render(sid: str) -> str:


	t = templates.get_template("chat/main.html")
	return t.render(
		contex={

		}
	)

@get("/", sync_to_thread=False)
def get_root(request: Request, sid: NamedDependency[str]) -> Response:
	t = templates.get_template("base.html")
	html = t.render({
		"body": render(sid),
		"updates_url": "/chat/updates",
	})
	return Response(
		content=html,
		media_type="text/html",
	)

@get("/chat/updates", sync_to_thread=False)
async def get_updates(request: Request, sid: NamedDependency[str]) -> Stream:
	return Stream(
		content=sse_generator(render, sid),
		media_type="text/event-stream",
		headers={
			"Cache-Control": "no-cache",
			"X-Accel-Buffering": "no",
		}
	)

router = Router(
	path="/",
	route_handlers=[
		get_root,
		get_updates,
	]
)