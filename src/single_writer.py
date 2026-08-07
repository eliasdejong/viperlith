import os, sys
from src.util.db_write_con import con
from src.util.frame_ticks import frame_ticks
from src.util.mpsc_queue import Q, drain
import src.util.mpsc_queue as mpsc


def writer_tick():
	with con:
		con.executemany(
			"INSERT or ignore into users (:session_id) values (?)",
			list(drain(Q.insert_user_q))
		)

		# Set 'starcord' as the default channel
		con.execute("""
			UPDATE users
			set current_channel_id = starcord_channel.id
			from (select id from channels where name = 'starcord') as starcord_channel
			where current_channel_id is NULL
		""")

		con.executemany("""
			INSERT into messages (channel_id, user_id, content)
			values (
				(select current_channel_id from users where session_id = :session_id),
				(select id from users where session_id = :session_id),
				:content
			)
		""", list(drain(Q.send_msg_q)))

def run_writer():
	try:
		mpsc.attach_all()
		frames = 0
		for _ in frame_ticks():
			writer_tick()
			if frames % (int(os.getenv("DB_ANALYZE_INTERVAL_HOURS")) * 3600 * int(os.getenv("FRAME_RATE"))) == 0: # every 4hrs
				con.pragma("optimize")
			frames += 1
	except (KeyboardInterrupt, Exception) as e:
		print(f"{type(e).__name__}: {e}")
		con.pragma("optimize", 0x00002)
		con.pragma("wal_checkpoint", "truncate")
		con.close()
		sys.exit(1)

if __name__ == "__main__":
	run_writer()