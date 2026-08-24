import os, random
from uuid import UUID, uuid4
from litestar import Request


if "SIMULATED_SESSION_COUNT_MAX" in os.environ:
	SIMULATED_SESSION_COUNT_MAX = int(os.getenv("SIMULATED_SESSION_COUNT_MAX"))
	def get_session_id() -> str:
		return f"s_{random.randint(1, SIMULATED_SESSION_COUNT_MAX):08d}"
else:
	def get_session_id(request: Request) -> str:
		try:
			return str(UUID(request.session.get("id")))
		except:
			sid = str(uuid4())
			request.session["id"] = sid
			return sid