import os
import asyncio
from collections.abc import AsyncGenerator
from src.util.db_write_con import con



async def sse_generator(render: Callable[..., str], *args, **kwargs) -> AsyncGenerator[str]:
	try:
		event_loop = asyncio.get_running_loop()
		frame_duration_sec = 1.0 / float(os.getenv("FRAME_RATE"))
		prev_data_version = None
		next_frame_time = event_loop.time()
		while True:
			next_frame_time += frame_duration_sec
			await asyncio.sleep(max(0.0, next_frame_time - event_loop.time()))

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
		print(f"Stream ended: {type(e).__name__}: {e}", flush=True)