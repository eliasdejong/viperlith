from collections.abc import Iterable

import apsw


def executemany_isolated(con: apsw.Connection, statements: str, items: Iterable[dict]) -> apsw.Cursor:
	# Each item runs inside a savepoint: a failing item is rolled back and
	# skipped, so one bad command cannot abort the batch. Any SQL failure is
	# an application bug, not a valid app state: isolate it, log it, move on.
	# Requires an open transaction (`with con:`); statements must end in ';'.
	it = iter(items)	# once: retries continue, never restart from item 0
	while True:
		try:
			return con.executemany(f"savepoint s; {statements} release s;", it)
		except apsw.Error as e:
			con.execute("rollback to s; release s;")
			# TODO: log to sentry: error=e
