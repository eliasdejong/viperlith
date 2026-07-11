import asyncio
from litestar import Router, get, post
from litestar.di import NamedDependency
from litestar.connection import Request
from litestar.response import Response, Stream

from collections.abc import AsyncGenerator

from src.util.jinja import templates


# state_changed_event = asyncio.Event()
# if notify:
# 	state_changed_event.set()
# 	state_changed_event.clear()

# next_frame_time = event_loop.time()
# next_frame_time += 1 / FRAME_RATE
# await asyncio.sleep(max(0, next_frame_time - event_loop.time()))


def render(sid: str) -> str:
	t = templates.get_template("chat/main.html")
	return t.render()

@get("/")
async def get_root(request: Request, sid: NamedDependency[str]) -> Response:
	t = templates.get_template("base.html")
	html = t.render({
		"body": render(sid),
		"updates_url": "/chat/updates",
	})
	return Response(
		content=html,
		media_type="text/html",
	)

async def updates_generator(sid: str) -> AsyncGenerator[str]:
	try:
		while True:
			html = render(sid)
			yield (
				"event: datastar-patch-elements\n"
				"data: selector body\n"
				"data: mode outer\n"
				"data: elements " + html.replace("\n", "\ndata: elements ")
				+ "\n\n"
			)
	except Exception as e:
	# except asyncio.CancelledError as e:
		print(f'Stream ended: {type(e).__name__}: {e}', flush=True)

@get("/chat/updates")
async def get_updates(request: Request, sid: NamedDependency[str]) -> Stream:
	return Stream(
		content=updates_generator(),
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
	]
)