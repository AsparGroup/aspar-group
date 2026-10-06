from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator


@contextmanager
def postgres_checkpointer(conn_string: str, setup: bool = False) -> Iterator[object]:
    """Yield a LangGraph PostgresSaver without committing credentials to Git.

    `setup=True` is intended for first-time database initialization only.
    """

    if not conn_string or not conn_string.strip():
        raise ValueError("A PostgreSQL connection string is required")

    from langgraph.checkpoint.postgres import PostgresSaver

    with PostgresSaver.from_conn_string(conn_string) as checkpointer:
        if setup:
            checkpointer.setup()
        yield checkpointer
