from typing import Any

from litestar import Router, get, post
from litestar.di import NamedDependency
from litestar.connection import Request
from litestar.response import Response, Stream
from litestar.response.base import ASGIResponse

import msgspec
import spsc_ring_threadsafe as srt

from src.util.jinja import templates
from src.util.db_read_con import con
from src.util.sse_generator import sse_generator
from src.util.mpsc_queue import Q
from src.util.msgpack_enc import msgpack_encoder

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
	model = InsertUser(session_id=sid)
	srt.put(Q.insert_user, msgpack_encoder.encode(model))
	return Stream(
		content=sse_generator(render, sid),
		media_type="text/event-stream",
		headers={
			"Cache-Control": "no-cache",
			"X-Accel-Buffering": "no",
		}
	)
import time
@post("/chat/send-message", sync_to_thread=False)
def post_send_msg(request: Request, sid: NamedDependency[str], signals_json: Any) -> ASGIResponse:
	time.sleep(2)
	model = send_msg_decoder.decode(signals_json).message
	model.session_id = sid
	srt.put(Q.send_msg, msgpack_encoder.encode(model))
	return ASGIResponse(status_code=204)

router = Router(
	path="/",
	route_handlers=[
		get_root,
		get_updates,
		post_send_msg,
	]
)