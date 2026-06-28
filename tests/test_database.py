from backend.database import DatabasePool, PooledConnection


class FakeCursor:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeRawConnection:
    def __init__(self):
        self.closed = False
        self.commits = 0
        self.rollbacks = 0
        self.cursor_instance = FakeCursor()

    def cursor(self, *_args, **_kwargs):
        return self.cursor_instance

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class FakeEngine:
    def __init__(self, raw):
        self.raw = raw

    def raw_connection(self):
        return self.raw


def test_connection_close_returns_raw_connection_once():
    raw = FakeRawConnection()
    pool = DatabasePool.__new__(DatabasePool)
    pool.engine = FakeEngine(raw)

    connection = pool.connect()
    cursor = connection.cursor()
    assert isinstance(connection, PooledConnection)
    assert cursor.connection is connection

    cursor.connection.commit()
    cursor.connection.close()
    cursor.connection.close()

    assert raw.commits == 1
    assert raw.closed is True
    assert raw.cursor_instance.closed is True


def test_context_manager_rolls_back_on_error():
    raw = FakeRawConnection()
    connection = PooledConnection(raw)

    try:
        with connection:
            raise ValueError("boom")
    except ValueError:
        pass

    assert raw.rollbacks == 1
    assert raw.closed is True
