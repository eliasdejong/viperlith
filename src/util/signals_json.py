from typing import Any
from litestar.connection import Request



async def signals_json(request: Request) -> dict[str, Any] | None:
	if "Datastar-Request" not in request.headers:
		return None
	if request.method in ("GET", "DELETE"):
		data = request.query_params.get("datastar")
	elif request.headers.get("Content-Type") == "application/json":
		data = await request.body()
	else:
		return None
	return data