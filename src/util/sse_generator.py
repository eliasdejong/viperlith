import asyncio
from collections.abc import AsyncGenerator
from src.util.db_read_con import data_version_events


async def sse_generator(render: Callable[..., Awaitable[str]], *args, **kwargs) -> AsyncGenerator[str, None]:
	event = asyncio.Event()
	data_version_events.add(event)
	try:
		while True:
			html = await render(*args, **kwargs)
			yield (
				"event: datastar-patch-elements\n"
				"data: selector body\n"
				"data: mode outer\n"
				"data: elements " + html.replace("\n", "\ndata: elements ")
				+ "\n\n"
			)
			await event.wait()
			event.clear()
	finally:
		data_version_events.discard(event)
