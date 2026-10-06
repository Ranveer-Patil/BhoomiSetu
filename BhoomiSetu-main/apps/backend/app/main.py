from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.intelligence import router as intelligence_router
from app.api.interoperability import router as interoperability_router
from app.api.operations import router as operations_router
from app.api.projects import router as projects_router
from app.core.config import settings

app = FastAPI(
    title="BhoomiSetu API",
    description="API for the BhoomiSetu SIH26016 prototype.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(intelligence_router)
app.include_router(interoperability_router)

app.include_router(operations_router)
