import os
import apsw
import apsw.bestpractice
apsw.bestpractice.apply(apsw.bestpractice.recommended)


con = apsw.Connection(
	os.getenv("DB_PATH"),
	flags=apsw.SQLITE_OPEN_READWRITE,
)
con.pragma("cache_size", 8192)
con.pragma("busy_timeout", 5000)
con.pragma("mmap_size", 281474976710655)
con.pragma("temp_store", "memory")

con.pragma("synchronous", "normal") # set to "full" if you cannot afford to lose 300ms of data on crash / power out
con.pragma("page_size", 4096)
