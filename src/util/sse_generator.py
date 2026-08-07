from collections.abc import AsyncGenerator
from src.util.db_read_con import con
from src.util.frame_ticks import frame_ticks_async


async def sse_generator(render: Callable[..., str], *args, **kwargs) -> AsyncGenerator[str, None]:
	try:
		prev_data_version = None
		async for _ in frame_ticks_async():
			data_version = con.pragma("data_version")
			if data_version == prev_data_version:
				continue
			prev_data_version = data_version
			yield (
				"event: datastar-patch-elements\n"
				"data: selector body\n"
				"data: mode outer\n"
				"data: elements " + render(*args, **kwargs).replace("\n", "\ndata: elements ")
				+ "\n\n"
			)
	except Exception as e:
		print(f"Stream ended: {type(e).__name__}: {e}")