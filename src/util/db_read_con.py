import os, itertools
import apsw
import apsw.bestpractice


apsw.shutdown()
apsw.config(apsw.mapping_config["SQLITE_CONFIG_MEMSTATUS"], False)
apsw.initialize()
apsw.bestpractice.apply(apsw.bestpractice.recommended)

DB_FILE_PATH = os.path.join(os.getenv("DB_PATH"), os.getenv("DB_FILE"))
POOL_SIZE = int(os.getenv("SQLITE_CONNECTION_COUNT_MAX")) // int(os.getenv("WEB_CONCURRENCY"))

utility_con = None
_connections = None
con_pool = None


async def con_create() -> apsw.AsyncConnection:
	con = await apsw.Connection.as_async(
		DB_FILE_PATH,
		flags=apsw.SQLITE_OPEN_READONLY
	)
	await con.pragma("cache_size", -1024) # 1 MiB
	await con.pragma("busy_timeout", 5000)
	await con.pragma("mmap_size", 281474976710655)
	await con.pragma("temp_store", "memory")
	return con

async def con_pool_create() -> None:
	global utility_con
	global _connections
	global con_pool
	utility_con = await apsw.Connection.as_async(
		DB_FILE_PATH,
		flags=apsw.SQLITE_OPEN_READONLY,
		statementcachesize=0,
	)
	_connections = [await con_create() for i in range(POOL_SIZE)]
	con_pool = itertools.cycle(_connections)
