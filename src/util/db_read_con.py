import os, asyncio, resource
# import time
from contextlib import AsyncExitStack
import apsw
import apsw.bestpractice

from src.util.frame_ticks import frame_ticks_async


apsw.shutdown()
apsw.config(apsw.mapping_config["SQLITE_CONFIG_MEMSTATUS"], False)
apsw.initialize()
apsw.bestpractice.apply(apsw.bestpractice.recommended)

DB_FILE_PATH = os.path.join(os.getenv("DB_PATH"), os.getenv("DB_FILE") + ".sqlite")
CON_POOL_SIZE_LOG2 = 2
CON_SCALE_IO_PAGE_THRESHOLD = 128

data_version_events = set()
utility_con = None

_connections = []
_ru_inblock = 0
_con_get_calls = 0
_con_idx_mask = 0


async def con_create() -> apsw.AsyncConnection:
	con = await apsw.Connection.as_async(
		DB_FILE_PATH,
		flags=apsw.SQLITE_OPEN_READONLY
	)
	await con.pragma("cache_size", -4096)
	await con.pragma("busy_timeout", 5000)
	await con.pragma("mmap_size", 4294967296)
	con.row_trace = apsw.ext.DataClassRowFactory(
		dataclass_kwargs={"frozen": True}
	)
	return con

async def con_pool_create() -> None:
	global utility_con
	global _connections
	utility_con = apsw.Connection(
		DB_FILE_PATH,
		flags=apsw.SQLITE_OPEN_READONLY,
		statementcachesize=0,
	)
	for i in range(2**CON_POOL_SIZE_LOG2):
		con = await con_create()
		_connections.append(con)

def con_get_by_sid(sid: str) -> apsw.AsyncConnection:
	global _ru_inblock
	global _con_get_calls
	global _con_idx_mask
	_con_get_calls += 1
	if (_con_get_calls & 0xff) == 0:
		current = resource.getrusage(resource.RUSAGE_SELF).ru_inblock
		# print(time.time(), current - _ru_inblock)
		if current - _ru_inblock > CON_SCALE_IO_PAGE_THRESHOLD:
			_con_idx_mask = 2**CON_POOL_SIZE_LOG2 - 1
		else:
			_con_idx_mask = 0
		_ru_inblock = current
	return _connections[hash(sid) & _con_idx_mask]

async def transaction_loop() -> None:
	ticks = frame_ticks_async().__aiter__()
	prev_version = None
	while True:
		version =  utility_con.pragma("data_version")
		async with AsyncExitStack() as batch:
			for con in _connections:
				await batch.enter_async_context(con)
			if version != prev_version:
				prev_version = version
				for event in data_version_events:
					event.set()
			await anext(ticks)
