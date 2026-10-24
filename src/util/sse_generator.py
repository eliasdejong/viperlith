from collections.abc import AsyncGenerator, Awaitable, Callable

from src.util.data_version import data_version_get, data_version_wait


async def sse_generator(render: Callable[..., Awaitable[str]], *args, **kwargs) -> AsyncGenerator[str, None]:
	seen = await data_version_get()
	while True:
		html = await render(*args, **kwargs)
		yield (
			"event: datastar-patch-elements\n"
			"data: selector body\n"
			"data: mode outer\n"
			"data: elements " + html.replace("\n", "\ndata: elements ")
			+ "\n\n"
		)
		seen = await data_version_wait(seen)
