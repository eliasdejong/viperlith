import os
from src.util.db_write_con import con



for fname in sorted(os.listdir("migrations")):
	if not fname.endswith(".sql"):
		continue
	migr_version = int(fname.split("_")[0])
	if migr_version > con.pragma("user_version"):
		with open(os.path.join("migrations", fname)) as f:
			con.execute(f.read())
		con.pragma("user_version", migr_version)
