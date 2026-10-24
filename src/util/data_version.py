import asyncio



_data_version_cond = asyncio.Condition()
_data_version = 0


async def data_version_get() -> int:
	async with _data_version_cond:
		return _data_version

async def data_version_bump() -> None:
	global _data_version
	async with _data_version_cond:
		_data_version += 1
		_data_version_cond.notify_all()

async def data_version_wait(seen_version: int) -> int:
	async with _data_version_cond:
		await _data_version_cond.wait_for(lambda: _data_version > seen_version)
		return _data_version
