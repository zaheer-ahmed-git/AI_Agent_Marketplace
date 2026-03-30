import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.graph.runtime import init_graph, shutdown_graph
from app.logging_mw import RequestLogMiddleware
from app.routers import agents, auth, health, marketplace, monitoring, tests, threads

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_graph()
    yield
    shutdown_graph()


def create_app() -> FastAPI:
    app = FastAPI(title="AI Agent Marketplace", version="1.0.0", lifespan=lifespan)
    app.add_middleware(RequestLogMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(agents.router)
    app.include_router(marketplace.router)
    app.include_router(threads.router)
    app.include_router(monitoring.router)
    app.include_router(tests.router)
    return app


app = create_app()
