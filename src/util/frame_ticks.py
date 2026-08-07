import os
import asyncio
import time
from typing import AsyncGenerator


FRAME_WAIT_TIME_SEC = 1.0 / float(os.getenv("FRAME_RATE"))

async def frame_ticks_async() -> AsyncGenerator[None, None]:
	event_loop = asyncio.get_running_loop()
	next_frame_time = event_loop.time()
	while True:
		yield
		next_frame_time += FRAME_WAIT_TIME_SEC
		await asyncio.sleep(max(0, next_frame_time - event_loop.time()))

def frame_ticks() -> Generator[None, None, None]:
	next_frame_time = time.perf_counter()
	while True:
		yield
		next_frame_time += FRAME_WAIT_TIME_SEC
		time.sleep(max(0, next_frame_time - time.perf_counter()))
