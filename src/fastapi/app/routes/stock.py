from app.schemas.stock import StockTsRecv, StockTsResp
from app.services.stock import predict_stock

from fastapi import APIRouter

router = APIRouter()


@router.post("/next_average_price", name="다음 분단위 가격 예측해보기", response_model=StockTsResp)
def stock_prediction(ts: StockTsRecv):
    pred_result = predict_stock(ts.model_name, ts.ticker_data)
    return {"next_average_price": pred_result}
