import os
from src.util.db_write_con import con
from src.util.db_migration import run_migration



SEED_CHANNEL_COUNT =	int(os.getenv("SEED_CHANNEL_COUNT"))
SEED_USER_COUNT =		int(os.getenv("SEED_USER_COUNT"))
SEED_MSG_COUNT =		int(os.getenv("SEED_MSG_COUNT"))
SEED_BENCH_SKEW = 		float(os.getenv("BENCH_SKEW"))

SEED_MSG_SIZE_MASK = 127

assert (
	SEED_CHANNEL_COUNT > 0
	and (SEED_CHANNEL_COUNT & (SEED_CHANNEL_COUNT - 1)) == 0
), "SEED_CHANNEL_COUNT must be a power of two"

assert (
	SEED_USER_COUNT > 0
	and (SEED_USER_COUNT & (SEED_USER_COUNT - 1)) == 0
), "SEED_USER_COUNT must be a power of two"

assert SEED_MSG_COUNT >= 0
assert 0.0 <= SEED_BENCH_SKEW < 1.0

MASK64 = (1 << 64) - 1



def mix64(x: int) -> int:
	x = (x + 0x9E3779B97F4A7C15) & MASK64
	x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
	x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & MASK64
	return (x ^ (x >> 31)) & MASK64

def zipf_rank(seed: int, count: int, alpha: float) -> int:
	u = (mix64(seed) >> 11) / float(1 << 53)
	p = 1.0 - alpha
	rank = (1.0 + u * (count ** p - 1.0)) ** (1.0 / p)
	return max(1, min(count, int(rank)))

def seed():
	print("Creating channels...")
	with con:
		con.executemany("""
			INSERT into channels (name)
			values (?)
			""",
			(
				(f"c_{channel_id:08d}",)
				for channel_id in range(1, SEED_CHANNEL_COUNT + 1)
			)
		)

	print("Creating users...")
	with con:
		con.execute("drop index if exists idx_users_session_id")
		con.executemany("""
			INSERT into users (
				nickname,
				session_id,
				current_channel_id
			)
			values (?, ?, ?)
			""",
			(
				(
					f"u_{user_id:08d}",
					f"s_{user_id:08d}",
					zipf_rank(
						user_id ^ 0x6fd8b0befdacc77a,
						SEED_CHANNEL_COUNT,
						SEED_BENCH_SKEW,
					),
				) for user_id in range(1, SEED_USER_COUNT + 1)
			)
		)
		con.execute("create index idx_users_session_id on users(session_id)")

	print("Creating channel memberships...")
	def membership_rows():
		for user_id in range(1, SEED_USER_COUNT + 1):
			current_channel_id = zipf_rank(
				user_id ^ 0x6fd8b0befdacc77a,
				SEED_CHANNEL_COUNT,
				SEED_BENCH_SKEW,
			)
			for offset in range(4):
				yield (
					user_id,
					current_channel_id if offset == 0 else 1 + (
						(current_channel_id - 1 + offset * 977) % SEED_CHANNEL_COUNT
					),
				)
	with con:
		con.execute("drop index if exists idx_channel_memberships_channel_id")
		con.executemany("""
			INSERT into channel_memberships (
				user_id,
				channel_id
			)
			values (?, ?)
			""",
			membership_rows(),
		)
		con.execute("create index idx_channel_memberships_channel_id on channel_memberships(channel_id)")

	print("Creating messages...")
	con.execute("drop index if exists idx_messages_channel_ts")

	def message_rows(start, end):
		for g in range(start, end):
			channel_id = zipf_rank(
				g ^ 0xa581c28479563caa,
				SEED_CHANNEL_COUNT,
				SEED_BENCH_SKEW,
			)
			user_id = 1 + (mix64(g ^ 0xdda62d587212b38b) & (SEED_USER_COUNT - 1))
			content = "a" * (mix64(g ^ 0xffd9962d6f73449e) & SEED_MSG_SIZE_MASK)
			created_ts = (
				1787155335.0 - 180 * 86400
				+ ((g * 7919) & 16777215) * (180 * 86400) / 16777215.0
			)
			yield (
				channel_id,
				user_id,
				content,
				created_ts,
			)

	COMMIT_BATCH_SIZE = 1_000_000
	rows_written = 0
	while rows_written < SEED_MSG_COUNT:
		batch_end = rows_written + min(COMMIT_BATCH_SIZE, SEED_MSG_COUNT - rows_written)
		with con:
			con.executemany("""
				INSERT into messages (
					channel_id,
					user_id,
					content,
					created_ts
				)
				values (?, ?, ?, ?)
				""",
				message_rows(rows_written, batch_end),
			)
		rows_written = batch_end
		print(f"Rows written: {rows_written} / {SEED_MSG_COUNT}")

	print("Creating index...")
	con.execute("create index idx_messages_channel_ts on messages(channel_id, created_ts)")

	print("Optimizing...")
	con.pragma("optimize", 0x10002)

	print("Truncating WAL...")
	con.pragma("wal_checkpoint", "truncate")

	page_count = con.pragma("page_count")
	page_size = con.pragma("page_size")
	db_bytes = page_count * page_size
	print()
	print(f"database size:  {db_bytes / (1000 ** 3):.3f} GB")
	print("============================================================")

if __name__ == "__main__":
	con.pragma("wal_autocheckpoint", 32768)
	print("Running migration...")
	run_migration()
	print("================= SEEDING BENCHMARK DATA =================")
	seed()