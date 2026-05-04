from fastapi import APIRouter

from app.api.v1.search import router as search_router

router = APIRouter()

@router.get("/health")
def api_health() -> dict[str, str]:
    return {"status": "ok"}


router.include_router(search_router)

api_router = router
