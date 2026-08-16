import os
from itertools import chain

from src.util.db_write_con import con
from src.util.frame_ticks import frame_ticks
from src.util.mpsc_queue import Q, drain
import src.util.mpsc_queue as mpsc
from src.util.db_migration import run_migration



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
			drain(Q.insert_user)
		)

		# Open channels
		con.executemany("""
			INSERT or ignore into channels (name)
			values (:name);

			insert or ignore into channel_memberships (user_id, channel_id)
			select u.id, (select id from channels where name = :name)
			from users u
			where u.session_id = :session_id;

			update users as u
			set current_channel_id = (select id from channels where name = :name)
			where u.session_id = :session_id;
			""",
			chain(
				({"name": "starcord", "session_id": u[0]} for u in new_users),
				drain(Q.open_channel),
			)
		)

		# Close channels
		con.executemany("""
			DELETE from channel_memberships as cm
			where user_id = (select id from users where session_id = :session_id)
				and channel_id = (select id from channels where name = :name)
			""",
			drain(Q.close_channel)
		)

		# Insert messages
		con.executemany("""
			INSERT into messages (channel_id, user_id, content)
			values (
				(select current_channel_id from users where session_id = :session_id),
				(select id from users where session_id = :session_id),
				:content
			)
			""",
			drain(Q.send_msg)
		)

		# Set nicknames
		con.executemany("""
			UPDATE users as u
			set nickname = :setNickname
			where session_id = :session_id
			""",
			drain(Q.set_nickname)
		)

def run_writer():
	run_migration()
	try:
		mpsc.attach_all()
		frames = 0
		for _ in frame_ticks():
			writer_tick()
			if frames % (int(os.getenv("DB_ANALYZE_INTERVAL_HOURS")) * 3600 * int(os.getenv("FRAME_RATE"))) == 0:
				con.pragma("optimize")
			frames += 1
	finally:
		con.pragma("optimize", 0x00002)
		con.pragma("wal_checkpoint", "truncate")
		con.close()

if __name__ == "__main__":
	run_writer()