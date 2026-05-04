from fastapi import FastAPI
from app.api.documents import router as documents_router
from app.api.error_handlers import register_exception_handlers
from app.api.health import router as health_router
from app.api.v1.router import api_router

app = FastAPI(title="Wissensbasis API", version="0.1.0")
register_exception_handlers(app)
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(api_router, prefix="/api/v1")
