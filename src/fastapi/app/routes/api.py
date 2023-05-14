from app.routes import stock

from fastapi import APIRouter

router = APIRouter()
router.include_router(stock.router, tags=["stock"], prefix="/stock")
