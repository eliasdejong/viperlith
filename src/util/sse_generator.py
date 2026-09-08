from collections.abc import AsyncGenerator
import src.util.db_read_con as db
from src.util.frame_ticks import frame_ticks_async


async def sse_generator(render: Callable[..., Awaitable[str]], *args, **kwargs) -> AsyncGenerator[str, None]:
	try:
		prev_version = None
		async for _ in frame_ticks_async():
			version =  db.utility_con.pragma("data_version")
			if version == prev_version:
				continue
			prev_version = version
			html = await render(*args, **kwargs)
			yield (
				"event: datastar-patch-elements\n"
				"data: selector body\n"
				"data: mode outer\n"
				"data: elements " + html.replace("\n", "\ndata: elements ")
				+ "\n\n"
			)
	except Exception as e:
		print(f"Stream ended: {type(e).__name__}: {e}")