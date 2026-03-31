import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import create_db
from app.routers import personas, relaciones, exportar, interpretar


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield


app = FastAPI(title="fac", description="Familia, amigos y conocidos", lifespan=lifespan)

app.include_router(personas.router)
app.include_router(relaciones.router)
app.include_router(exportar.router)
app.include_router(interpretar.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def root():
    return FileResponse("app/static/index.html")
