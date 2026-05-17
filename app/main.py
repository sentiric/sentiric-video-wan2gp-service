import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logging_utils import setup_logging
from app.core.engine import wan_engine
from app.grpc_server import serve_grpc

setup_logging("video-wan2gp-service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Model yüklemesi (Swap sayesinde Killed almayacak)
    wan_engine.initialize()
    # gRPC sunucusu başlat
    grpc_task = asyncio.create_task(serve_grpc())
    yield
    grpc_task.cancel()

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

@app.get("/healthz")
def health():
    return {"status": "ok", "service": "video-wan2gp-service"}