import os
from src.util.db_write_con import con


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MIGRATIONS_DIR = os.path.join(CURRENT_DIR, "../../migrations")


def run_migration():
	for fname in sorted(os.listdir(MIGRATIONS_DIR)):
		if not fname.endswith(".sql"):
			continue
		migr_version = int(fname.split("_")[0])
		if migr_version > con.pragma("user_version"):
			with open(os.path.join(MIGRATIONS_DIR, fname)) as f:
				con.execute(f.read())
			con.pragma("user_version", migr_version)

if __name__ == "__main__":
	run_migration()