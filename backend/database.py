import os
from threading import Lock

from sqlalchemy import URL, create_engine


class PooledCursor:
    def __init__(self, cursor, connection):
        self._cursor = cursor
        self.connection = connection

    def close(self):
        self._cursor.close()

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class PooledConnection:
    def __init__(self, raw_connection):
        self._raw_connection = raw_connection
        self._cursors = []
        self._closed = False
        self._lock = Lock()

    def cursor(self, *args, **kwargs):
        cursor = PooledCursor(
            self._raw_connection.cursor(*args, **kwargs),
            self,
        )
        self._cursors.append(cursor)
        return cursor

    def commit(self):
        self._raw_connection.commit()

    def rollback(self):
        self._raw_connection.rollback()

    def close(self):
        with self._lock:
            if self._closed:
                return
            for cursor in self._cursors:
                try:
                    cursor.close()
                except Exception:
                    pass
            self._raw_connection.close()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, _exc, _traceback):
        try:
            if exc_type is not None:
                self.rollback()
        finally:
            self.close()


class DatabasePool:
    def __init__(self, config):
        url = URL.create(
            "mysql+pymysql",
            username=config["user"],
            password=config["password"],
            host=config["host"],
            port=config["port"],
            database=config["database"],
            query={"charset": config.get("charset", "utf8mb4")},
        )
        self.engine = create_engine(
            url,
            pool_size=int(os.environ.get("DB_POOL_SIZE", "5")),
            max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "5")),
            pool_timeout=int(os.environ.get("DB_POOL_TIMEOUT", "10")),
            pool_recycle=int(os.environ.get("DB_POOL_RECYCLE", "1800")),
            pool_pre_ping=True,
        )

    def connect(self):
        return PooledConnection(self.engine.raw_connection())

    def status(self):
        return self.engine.pool.status()

    def dispose(self):
        self.engine.dispose()
