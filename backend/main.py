from config import settings
from database import shutdown, startup
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from middlewares import SessionMiddleware
from routers import auth, bots, users


def create_app() -> FastAPI:
    app = FastAPI(
        title="AutoSinan",
        description="Uma coleção de bots para automatizar tarefas no Sinan Online",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        on_startup=[startup],
        on_shutdown=[shutdown],
    )

    app.add_middleware(SessionMiddleware)

    app.include_router(auth.router, prefix="/auth", tags=["Auth"])
    app.include_router(users.router, prefix="/users", tags=["Users"])
    app.include_router(bots.router, prefix="/bots", tags=["Bots"])

    @app.get("/")
    async def root():
        return RedirectResponse(url="/docs")

    return app


app = create_app()
