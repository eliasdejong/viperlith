import os
import apsw



if __name__ == "__main__":
	con = apsw.Connection(
		os.path.join(os.getenv("DB_PATH"), os.getenv("DB_FILE")),
		flags=apsw.SQLITE_OPEN_READWRITE | apsw.SQLITE_OPEN_CREATE,
	)
	for fname in sorted(os.listdir("schema/migrations")):
		if not fname.endswith(".sql"):
			continue
		migr_version = int(fname.split("_")[0])
		if migr_version > con.pragma("user_version"):
			with open(os.path.join("schema/migrations", fname)) as f:
				con.execute(f.read())
			con.pragma("user_version", migr_version)
	con.close()
