import os
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

con.pragma("synchronous", "normal") # set to "full" if you cannot afford to lose ~300ms of data on crash / power out
con.pragma("page_size", 32768)
con.pragma("optimize", 0x10002)

# # Run before shutting down
# con.pragma("optimize", 0x00002)
# con.pragma("wal_checkpoint", "truncate")

async def db_analyze_loop(con: apsw.Connection, interval_hours: int):
	while True:
		await asyncio.sleep(interval_hours * 3600)
		try:
			con.pragma("optimize", 0x00002)
		except Exception:
			pass

# asyncio.create_task(analyze_loop(con, os.getenv("DB_ANALYZE_INTERVAL_HOURS")))