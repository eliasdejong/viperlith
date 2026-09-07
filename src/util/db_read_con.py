import os, asyncio
import apsw
import apsw.bestpractice


apsw.shutdown()
apsw.config(apsw.mapping_config["SQLITE_CONFIG_MEMSTATUS"], False)
apsw.initialize()
apsw.bestpractice.apply(apsw.bestpractice.recommended)

DB_FILE_PATH = os.path.join(os.getenv("DB_PATH"), os.getenv("DB_FILE") + ".sqlite")
CON_POOL_SIZE = 4

utility_con = None
_connections = []


async def con_create() -> apsw.AsyncConnection:
	con = await apsw.Connection.as_async(
		DB_FILE_PATH,
		flags=apsw.SQLITE_OPEN_READONLY
	)
	await con.pragma("cache_size", -4096)
	await con.pragma("busy_timeout", 5000)
	await con.pragma("mmap_size", 4294967296)
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
		_connections.append(con)

def con_get_by_sid(sid: str) -> apsw.AsyncConnection:
	return _connections[hash(sid) % CON_POOL_SIZE]