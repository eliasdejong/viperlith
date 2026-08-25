import os
import apsw
import apsw.bestpractice


apsw.shutdown()
apsw.config(apsw.mapping_config["SQLITE_CONFIG_MEMSTATUS"], False)
apsw.initialize()
apsw.bestpractice.apply(apsw.bestpractice.recommended)


con = apsw.Connection(
	os.path.join(os.getenv("DB_PATH"), os.getenv("DB_FILE")),
	flags=apsw.SQLITE_OPEN_READONLY,
)
con.pragma("cache_size", 8192) # 32 MiB
con.pragma("busy_timeout", 5000)
con.pragma("mmap_size", 281474976710655)
con.pragma("temp_store", "memory")