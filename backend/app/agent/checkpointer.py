"""PostgreSQL LangGraph Checkpointer Management."""

import logging
from typing import Tuple
from fastapi import Request, HTTPException, status
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.postgres import PostgresSaver

from backend.app.config import settings

logger = logging.getLogger("checkpointer")


def init_postgres_checkpointer_tables():
    """Ensure LangGraph checkpoint tables are initialized in PostgreSQL."""
    try:
        conn_str = settings.sync_database_url
        with PostgresSaver.from_conn_string(conn_str) as saver:
            saver.setup()
            logger.info("LangGraph PostgreSQL checkpoint tables verified successfully.")
    except Exception as e:
        logger.warning("Checkpointer setup notice: %s", e)


async def create_checkpointer_pool() -> Tuple[AsyncConnectionPool, AsyncPostgresSaver]:
    """Create and open a shared AsyncConnectionPool and AsyncPostgresSaver for the app lifespan."""
    conn_str = settings.sync_database_url
    pool = AsyncConnectionPool(
        conninfo=conn_str,
        max_size=10,
        kwargs={"autocommit": True},
        open=False,
    )
    await pool.open()
    await pool.wait()
    checkpointer = AsyncPostgresSaver(pool)
    return pool, checkpointer


def get_checkpointer_dep(request: Request) -> AsyncPostgresSaver:
    """Dependency to retrieve the shared AsyncPostgresSaver from app.state."""
    checkpointer = getattr(request.app.state, "checkpointer", None)
    if not checkpointer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat checkpointer is not initialized.",
        )
    return checkpointer


# Alias for convenience
get_checkpointer = get_checkpointer_dep
