from psycopg_pool import ConnectionPool

from app.core.database import get_database_url

pool: ConnectionPool | None = None


def open_pool() -> ConnectionPool:
    global pool
    if pool is None:
        pool = ConnectionPool(conninfo=get_database_url(), open=False)
    pool.open()
    return pool


def close_pool() -> None:
    if pool is not None:
        pool.close()
