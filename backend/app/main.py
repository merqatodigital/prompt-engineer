from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import Base, engine
from .routes import chat, prompts, settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Prompt Engineer API", version="0.4.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_error(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "Unexpected server error.", "details": type(exc).__name__}})


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


app.include_router(chat.router)
app.include_router(prompts.router)
app.include_router(settings.router)
