from psycopg_pool import ConnectionPool
from app.core.config import settings

pool = ConnectionPool(
    conninfo=settings.database_url.replace("postgresql+psycopg://", "postgresql://"),
    open=False,
)

def open_pool() -> None:
    pool.open()

def close_pool() -> None:
    pool.close()
