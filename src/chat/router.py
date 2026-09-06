from typing import Any

from litestar import Router, get, post
from litestar.di import NamedDependency
from litestar.connection import Request
from litestar.response import Stream

import apsw
import msgspec
import spsc_ring_threadsafe as srt

from src.util.db_read_con import con_get_by_sid
from src.util.jinja import templates
from src.util.sse_generator import sse_generator
from src.util.mpsc_queue import Q
from src.util.msgpack_enc import msgpack_encoder

from src.chat.types import *



def _render_sync(con: apsw.Connection, sid: str) -> str:
	t = templates.get_template("chat/main.html")
	with con:
		return t.render(con=con, sid=sid)

async def render(sid: str) -> str:
	con = con_get_by_sid(sid)
	return await con.async_run(_render_sync, con, sid)

@get("/", media_type="text/html")
async def get_root(request: Request, sid: NamedDependency[str]) -> str:
	t = templates.get_template("base.html")
	return t.render(
		body=await render(sid),
		updates_url="/chat/updates"
	)

@get("/chat/updates")
async def get_updates(request: Request, sid: NamedDependency[str]) -> Stream:
	model = UserInsert(session_id=sid)
	srt.put(Q.user_insert, msgpack_encoder.encode(model))
	return Stream(
		content=sse_generator(render, sid),
		media_type="text/event-stream",
		headers={
			"Cache-Control": "no-cache",
			"X-Accel-Buffering": "no",
		}
	)

@post("/chat/message-send", sync_to_thread=False, status_code=204)
def post_msg_send(request: Request, sid: NamedDependency[str], signals_json: Any) -> None:
	model = msg_send_decoder.decode(signals_json)
	model.session_id = sid
	srt.put(Q.msg_send, msgpack_encoder.encode(model))

@post("/chat/channel-open", sync_to_thread=False, status_code=204)
def post_channel_open(request: Request, sid: NamedDependency[str], signals_json: Any) -> None:
	model = channel_open_decoder.decode(signals_json)
	model.session_id = sid
	srt.put(Q.channel_open, msgpack_encoder.encode(model))

@post("/chat/channel-open/validate", sync_to_thread=False, status_code=200)
def post_channel_open_validate(request: Request, signals_json: Any) -> dict[str, str]:
	try:
		channel_open_decoder.decode(signals_json)
		return {"_channelOpenError": ""}
	except msgspec.ValidationError as e:
		return {"_channelOpenError": "Invalid channel name"}

@post("/chat/channel-close", sync_to_thread=False, status_code=204)
def post_channel_close(request: Request, sid: NamedDependency[str], signals_json: Any) -> None:
	model = channel_close_decoder.decode(signals_json)
	model.session_id = sid
	srt.put(Q.channel_close, msgpack_encoder.encode(model))

@post("/chat/nickname-set", sync_to_thread=False, status_code=200)
def post_nickname_set(request: Request, sid: NamedDependency[str], signals_json: Any) -> dict[str, str]:
	try:
		model = nickname_set_decoder.decode(signals_json)
		model.session_id = sid
		srt.put(Q.nickname_set, msgpack_encoder.encode(model))
		return {"_nicknameSetError": ""}
	except msgspec.ValidationError as e:
		return {"_nicknameSetError": "Allowed characters: 'A-Za-z0-9 _-'"}
	
router = Router(
	path="/",
	route_handlers=[
		get_root,
		get_updates,
		post_msg_send,
		post_channel_open,
		post_channel_open_validate,
		post_channel_close,
		post_nickname_set,
	]
)