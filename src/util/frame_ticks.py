import os
import asyncio
from typing import AsyncGenerator


async def frame_ticks() -> AsyncGenerator[None, None]:
	event_loop = asyncio.get_running_loop()
	next_frame_time = event_loop.time()
	frame_duration_sec = 1.0 / float(os.getenv("FRAME_RATE"))
	while True:
		yield
		next_frame_time += frame_duration_sec
		await asyncio.sleep(max(0, next_frame_time - event_loop.time()))