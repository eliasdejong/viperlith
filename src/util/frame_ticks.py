import os, asyncio
from time import sleep, perf_counter
from typing import AsyncGenerator


FRAME_WAIT_TIME_SEC = 1.0 / float(os.getenv("FRAME_RATE"))

async def frame_ticks_async() -> AsyncGenerator[None, None]:
	loop = asyncio.get_running_loop()
	while True:
		next_time = loop.time() + FRAME_WAIT_TIME_SEC
		yield
		await asyncio.sleep(max(0.0, next_time -  loop.time()))

def frame_ticks() -> Generator[None, None, None]:
	while True:
		next_time = perf_counter() + FRAME_WAIT_TIME_SEC
		yield
		sleep(max(0.0, next_time - perf_counter()))
