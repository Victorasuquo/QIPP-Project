from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.mongodb import connect_mongodb, disconnect_mongodb
from app.middleware import TenantContextMiddleware, OrgScopingMiddleware, SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_mongodb()
    yield
    # Shutdown
    await disconnect_mongodb()


def create_app() -> FastAPI:
    app = FastAPI(
        title="QIPP Medicines Optimisation API",
        description="Live backend for the QIPP platform — South Yorkshire ICB",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        # Allow localhost on any port for local Vite dev and Vercel preview/prod domains.
        allow_origin_regex=r"https://.*\.vercel\.app|http://localhost(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Custom middleware (order matters — outermost first) ───────────────────
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(OrgScopingMiddleware)
    app.add_middleware(TenantContextMiddleware)

    # ── Routers ───────────────────────────────────────────────────────────────
    from app.routers.auth import router as auth_router
    from app.routers.dashboard import router as dashboard_router
    from app.routers.opportunities import router as opportunities_router
    from app.routers.practices import router as practices_router
    from app.routers.interventions import router as interventions_router
    from app.routers.savings import router as savings_router
    from app.routers.admin import router as admin_router
    from app.routers.ai_search import router as ai_search_router
    from app.routers.documents import router as documents_router
    from app.routers.notifications import router as notifications_router

    app.include_router(auth_router, prefix=settings.API_PREFIX)
    app.include_router(dashboard_router, prefix=settings.API_PREFIX)
    app.include_router(opportunities_router, prefix=settings.API_PREFIX)
    app.include_router(practices_router, prefix=settings.API_PREFIX)
    app.include_router(interventions_router, prefix=settings.API_PREFIX)
    app.include_router(savings_router, prefix=settings.API_PREFIX)
    app.include_router(admin_router, prefix=settings.API_PREFIX)
    app.include_router(ai_search_router, prefix=settings.API_PREFIX)
    app.include_router(documents_router, prefix=settings.API_PREFIX)
    app.include_router(notifications_router, prefix=settings.API_PREFIX)

    # Health check
    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok", "version": "1.0.0", "env": settings.APP_ENV}

    return app


app = create_app()
