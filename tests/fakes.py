"""Fake MySQL connection layer used to unit test routes without a real database."""


class FakeCursor:
    """A cursor backed by a shared result stream on its connection.

    ``fetchone``/``fetchall`` pull the next items from the connection's shared
    scripted stream, in order, matching how a real scripted database session
    would return rows across consecutive queries.  Every executed statement is
    recorded on the cursor so tests can assert on the generated SQL and params.
    """

    def __init__(self, connection):
        self.connection = connection
        self.lastrowid = getattr(connection, "lastrowid", 1)
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return None

    def executemany(self, sql, params=None):
        self.executed.append((sql, params))
        return None

    def fetchone(self):
        return self.connection._take()

    def fetchall(self):
        result = self.connection._take()
        return result if result is not None else []

    def close(self):
        pass


class FakeConnection:
    """Mimics a database connection.

    ``scripted`` is a list of results (rows / dicts) consumed in order by all
    cursors created from this connection.  Tests build the connection with the
    exact sequence of results the route under test expects.
    """

    def __init__(self, scripted=None):
        self.scripted = list(scripted or [])
        self.lastrowid = 1
        self._index = 0
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self.cursors = []

    def cursor(self, dictionary=False):
        cursor = FakeCursor(self)
        self.cursors.append(cursor)
        return cursor

    def _take(self):
        if self._index < len(self.scripted):
            item = self.scripted[self._index]
            self._index += 1
            return item
        return None

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True
