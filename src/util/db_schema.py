import os
import apsw


con = apsw.Connection(
	os.getenv("DB_PATH"),
	flags=apsw.SQLITE_OPEN_READWRITE,
)
with open('schema/schema.sql') as f:
	con.execute(f.read())
con.close()