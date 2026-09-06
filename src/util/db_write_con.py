import os
import apsw
import apsw.bestpractice


apsw.shutdown()
apsw.config(apsw.mapping_config["SQLITE_CONFIG_MEMSTATUS"], False)
apsw.initialize()
apsw.bestpractice.apply(apsw.bestpractice.recommended)

con = apsw.Connection(
	os.path.join(os.getenv("DB_PATH"), os.getenv("DB_FILE") + ".sqlite"),
	flags=apsw.SQLITE_OPEN_READWRITE | apsw.SQLITE_OPEN_CREATE,
)
con.pragma("page_size", 4096)
con.pragma("journal_mode", "wal")
con.pragma("journal_size_limit", 33554432) # 32 MiB; prevent WAL from growing unbounded
con.pragma("synchronous", "normal")

con.pragma("cache_size", -32768)
con.pragma("busy_timeout", 5000)
con.pragma("mmap_size", 4294967296)
