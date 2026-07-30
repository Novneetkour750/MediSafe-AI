from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from routes import chat, health, reference, scan
from utils.exceptions import MediSafeError
from utils.logger import get_logger

log = get_logger("app")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="MediSafe AI API", version="2.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(MediSafeError)
    def handle_medisafe_error(_: Request, exc: MediSafeError) -> JSONResponse:
        log.warning("%s: %s", type(exc).__name__, exc)
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    app.include_router(health.router)
    app.include_router(reference.router)
    app.include_router(scan.router)
    app.include_router(chat.router)

    @app.get("/")
    def root():
        return {"message": "MediSafe AI API", "docs": "/docs"}

    return app


app = create_app()
