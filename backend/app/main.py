"""FastAPI Main Application Entrypoint."""

import sys
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.agent.checkpointer import (
    init_postgres_checkpointer_tables,
    create_checkpointer_pool,
)
from backend.app.config import settings
from backend.app.database import init_db
from backend.app.routes import (
    auth_router,
    branches_router,
    chat_router,
    customer_orders_router,
    staff_auth_router,
    staff_branches_router,
    staff_menu_router,
    staff_orders_router,
    staff_reservations_router,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("restaurant_ai_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown events."""
    logger.info("Starting Multi-Branch Restaurant AI Agent Backend...")
    pool = None
    try:
        await init_db()
        init_postgres_checkpointer_tables()
        pool, checkpointer = await create_checkpointer_pool()
        app.state.checkpointer_pool = pool
        app.state.checkpointer = checkpointer
        logger.info("Database and Checkpointer initialized successfully.")
    except Exception as e:
        logger.error("Startup DB initialization notice: %s", e)

    yield

    logger.info("Shutting down Multi-Branch Restaurant AI Agent Backend...")
    if pool:
        try:
            await pool.close()
            logger.info("Checkpointer connection pool closed successfully.")
        except Exception as e:
            logger.error("Error closing checkpointer connection pool: %s", e)


app = FastAPI(
    title="Multi-Branch Restaurant AI Agent API",
    description="Conversational Multi-Branch Restaurant AI Agent with LangGraph and DeepSeek R1 8B",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits chat widget embedding from any domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(staff_auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(branches_router, prefix="/api")
app.include_router(customer_orders_router, prefix="/api")
app.include_router(staff_branches_router, prefix="/api")
app.include_router(staff_menu_router, prefix="/api")
app.include_router(staff_orders_router, prefix="/api")
app.include_router(staff_reservations_router, prefix="/api")


@app.get("/health")
def health_check():
    """Health check endpoint for cloud hosting / Docker healthchecks."""
    return {"status": "ok", "environment": settings.ENVIRONMENT, "model": settings.OLLAMA_MODEL}
