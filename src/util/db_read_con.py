import os, asyncio
from contextlib import asynccontextmanager
import apsw
import apsw.bestpractice
from src.util.frame_ticks import frame_ticks_async


apsw.shutdown()
apsw.config(apsw.mapping_config["SQLITE_CONFIG_MEMSTATUS"], False)
apsw.initialize()
apsw.bestpractice.apply(apsw.bestpractice.recommended)

DB_FILE_PATH = os.path.join(os.getenv("DB_PATH"), os.getenv("DB_FILE") + ".sqlite")
CON_POOL_SIZE = 1

utility_con = None
_con_pool = asyncio.Queue()
_connections = []


async def con_create() -> apsw.AsyncConnection:
	con = await apsw.Connection.as_async(
		DB_FILE_PATH,
		flags=apsw.SQLITE_OPEN_READONLY
	)
	await con.pragma("cache_size", -8192)
	await con.pragma("busy_timeout", 5000)
	# await con.pragma("mmap_size", 4294967296)
	# await con.pragma("mmap_size", 40000000000)
	await con.pragma("mmap_size", 281474976710655)
	return con

async def con_pool_create() -> None:
	global utility_con
	global _connections
	utility_con = await apsw.Connection.as_async(
		DB_FILE_PATH,
		flags=apsw.SQLITE_OPEN_READONLY,
		statementcachesize=0,
	)
	for i in range(CON_POOL_SIZE):
		con = await con_create()
		_con_pool.put_nowait(con)
		_connections.append(con)

@asynccontextmanager
async def read_connection() -> apsw.AsyncConnection:
	con = await _con_pool.get()
	try:
		yield con
	finally:
		_con_pool.put_nowait(con)

async def transaction_commit_loop() -> None:
	await asyncio.gather(*(con.execute("BEGIN") for con in _connections))
	async for _ in frame_ticks_async():
		await asyncio.gather(*(
			con.execute("COMMIT; BEGIN;") for con in _connections
		))