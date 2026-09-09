import os
from itertools import chain

from src.util.db_write_con import con
from src.util.frame_ticks import frame_ticks
from src.util.mpsc_queue import Q, drain
import src.util.mpsc_queue as mpsc



DB_ANALYZE_INTERVAL_HOURS = int(os.getenv("DB_ANALYZE_INTERVAL_HOURS"))
FRAME_RATE = int(os.getenv("FRAME_RATE"))



def writer_tick():
	with con:
		# Insert new users
		new_users = con.executemany("""
			INSERT or ignore into users (session_id, current_channel_id)
			values (
				:session_id,
				(select id from channels where name = 'starcord')
			)
			returning session_id
			""",
			drain(Q.user_insert)
		)

		# Open channels
		con.executemany("""
			INSERT or ignore into channels (name)
			values (:channelOpen);

			insert or ignore into channel_memberships (user_id, channel_id)
			select u.id, (select id from channels where name = :channelOpen)
			from users u
			where u.session_id = :session_id;

			update users as u
			set current_channel_id = (select id from channels where name = :channelOpen)
			where u.session_id = :session_id;
			""",
			chain(
				({"channelOpen": "starcord", "session_id": u[0]} for u in new_users),
				drain(Q.channel_open),
			)
		)

		# Close channels
		con.executemany("""
			DELETE from channel_memberships as cm
			where user_id = (select id from users where session_id = :session_id)
				and channel_id = (select id from channels where name = :channelClose)
			""",
			drain(Q.channel_close)
		)

		# Insert messages
		con.executemany("""
			INSERT into messages (channel_id, user_id, content)
			values (
				(select current_channel_id from users where session_id = :session_id),
				(select id from users where session_id = :session_id),
				:messageSend
			)
			""",
			drain(Q.msg_send)
		)

		# Set nicknames
		con.executemany("""
			UPDATE users as u
			set nickname = :nicknameSet
			where session_id = :session_id
			""",
			drain(Q.nickname_set)
		)
	con.pragma("wal_checkpoint", "restart")

def run_writer():
	print("Optimizing database...")
	con.pragma("optimize", 0x10002)
	print("Attaching to shared memory...")
	mpsc.attach_all()
	frames = 0
	for _ in frame_ticks():
		writer_tick()
		if frames % (DB_ANALYZE_INTERVAL_HOURS * 3600 * FRAME_RATE) == 0:
			con.pragma("optimize")
		frames += 1

if __name__ == "__main__":
	run_writer()