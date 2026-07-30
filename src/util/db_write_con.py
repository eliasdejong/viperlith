import os
import asyncio
import apsw
import apsw.bestpractice
apsw.bestpractice.apply(apsw.bestpractice.recommended)


con = apsw.Connection(
	os.path.join(os.getenv("DB_PATH"), os.getenv("DB_FILE")),
	flags=apsw.SQLITE_OPEN_READWRITE | apsw.SQLITE_OPEN_CREATE,
)
con.pragma("cache_size", 8192)
con.pragma("busy_timeout", 5000)
con.pragma("mmap_size", 281474976710655)
con.pragma("temp_store", "memory")

con.pragma("journal_size_limit", 67108864) # ~64MiB; prevent WAL from growing unbounded
con.pragma("synchronous", "normal") # set to "full" if you cannot afford to lose ~300ms of data on crash / power out
con.pragma("page_size", 32768)
con.pragma("optimize", 0x10002)


async def db_analyze_loop(con: apsw.Connection, interval_hours: int):
	while True:
		await asyncio.sleep(interval_hours * 3600)
		try:
			con.pragma("optimize", 0x00010)
		except Exception:
			pass