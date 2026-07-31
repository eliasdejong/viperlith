from uuid import UUID, uuid4
from litestar import Request


def get_session_id(request: Request) -> str:
	try:
		return str(UUID(request.session.get("id")))
	except:
		sid = str(uuid4())
		request.session["id"] = sid
		return sid