from fastapi import FastAPI, Request
from typing import Optional
import os


app = FastAPI(
    title="Constitución de Panamá API",
    version="1.0.0",
    description=(
        "API REST para consultar y gestionar datos de la Constitución de Panamá.\n\n"
        "Primeros pasos:\n"
        "- Arranca el servidor: `uvicorn main:app --reload`.\n"
        "- Usa Swagger UI en `/docs`.\n"
        "- Endpoints: `/constitucion`, `/titulos`, `/capitulos`, `/articulos`.\n"
        "- Autenticación básica requerida para POST/PUT/DELETE de artículos."
    ),
    contact={
        "name": "ACT Panamá",
        "url": "https://actpanama.com",
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    openapi_tags=[
        {
            "name": "Constitución",
            "description": "Acceso al documento completo de la Constitución.",
        },
        {
            "name": "Títulos",
            "description": "Operaciones relacionadas con los Títulos del texto constitucional.",
        },
        {
            "name": "Capítulos",
            "description": "Operaciones de consulta sobre Capítulos dentro de cada Título.",
        },
        {
            "name": "Artículos",
            "description": "Listado, detalle y operaciones CRUD de Artículos.",
        },
        {
            "name": "Sistema",
            "description": "Rutas básicas de salud y utilidades del servicio.",
        },
    ],
)

from routes.constitucion import router as constitucion_router

app.include_router(constitucion_router)


@app.get(
    "/status",
    summary="Estado del servicio",
    tags=["Sistema"],
    description="Verifica el estado del servicio y conectividad.",
)
async def status(request: Request):
    return {"status": "ok"}


@app.get("/", summary="Raíz", tags=["Sistema"], description="Ruta raíz del servicio.")
async def root(request: Request):
    return {"message": "Constitución de Panamá API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
