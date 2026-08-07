from litestar import Router, get, post
from litestar.di import NamedDependency
from litestar.connection import Request
from litestar.response import Response, Stream
from litestar.response.base import ASGIResponse

import msgspec
from typing import Any

from src.util.jinja import templates
from src.util.db_read_con import con
from src.util.sse_generator import sse_generator

from src.chat.types import *



def render(sid: str) -> str:
	t = templates.get_template("chat/main.html")
	with con:
		ret = t.render(con=con, sid=sid)
	return ret

@get("/", sync_to_thread=False)
def get_root(request: Request, sid: NamedDependency[str]) -> Response:
	t = templates.get_template("base.html")
	html = t.render(body=render(sid), updates_url="/chat/updates")
	return Response(
		content=html,
		media_type="text/html",
	)

@get("/chat/updates")
async def get_updates(request: Request, sid: NamedDependency[str]) -> Stream:
	# insert_user_arr.append((sid,))
	return Stream(
		content=sse_generator(render, sid),
		media_type="text/event-stream",
		headers={
			"Cache-Control": "no-cache",
			"X-Accel-Buffering": "no",
		}
	)

msg_decoder = msgspec.json.Decoder(type=MessageOuter)

@post("/chat/send-message", sync_to_thread=False)
def post_send_msg(request: Request, sid: NamedDependency[str], signals_json: Any) -> ASGIResponse:
	# msg = msg_decoder.decode(signals_json).message
	# msg.session_id = sid
	# send_msg_arr.append(msgspec.to_builtins(msg))
	return ASGIResponse(status_code=204)

router = Router(
	path="/",
	route_handlers=[
		get_root,
		get_updates,
		post_send_msg,
	]
)