from collections.abc import Iterable

import apsw


def executemany_isolated(con: apsw.Connection, statements: str, items: Iterable[dict]) -> apsw.Cursor:
	it = iter(items)
	while True:
		try:
			return con.executemany(f"savepoint s; {statements}; release s;", it)
		except apsw.Error as e:
			con.execute("rollback to s; release s;")
