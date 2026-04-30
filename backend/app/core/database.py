from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg import Connection

from app.core.config import settings


class DatabaseConfigurationError(RuntimeError):
    pass


def get_database_url() -> str:
    if not settings.database_url:
        raise DatabaseConfigurationError("DATABASE_URL is not configured")
    return settings.database_url.replace("postgresql+psycopg://", "postgresql://")


def get_sqlalchemy_database_url() -> str:
    if not settings.database_url:
        raise DatabaseConfigurationError("DATABASE_URL is not configured")
    if settings.database_url.startswith("postgresql://"):
        return settings.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return settings.database_url


@contextmanager
def get_connection() -> Iterator[Connection]:
    with psycopg.connect(get_database_url(), connect_timeout=5) as connection:
        yield connection


def check_database_connection() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("select 1")
            cursor.fetchone()
