"""Aplicación FastAPI de PoliTracker."""
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers import gasto, ingreso

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("politracker")

app = FastAPI(
    title="PoliTracker API",
    description="Datos abiertos del Presupuesto General de la Nación de Colombia, "
                "en formato pensado para ciudadanos.",
    version="0.1.0",
)

origins = ["http://localhost:5173"]
extra = os.getenv("FRONTEND_ORIGIN", "").strip()
if extra and extra not in origins:
    origins.append(extra)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(gasto.router)
app.include_router(ingreso.router)


@app.exception_handler(Exception)
async def manejador_global(request: Request, exc: Exception):
    """Nunca devolver un 500 pelado: loggea el detalle y responde con contexto."""
    logger.exception("Error no manejado en %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor. Revisa los logs del backend."},
    )


@app.get("/")
def raiz():
    return {"servicio": "PoliTracker API", "docs": "/docs"}
