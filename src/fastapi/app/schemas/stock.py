from typing import Dict, List

from pydantic import BaseModel


class StockTsRecv(BaseModel):
    model_name: str
    ticker_data: Dict

    class Config:
        schema_extra = {
            "example": {
                "model_name": "ETH-Model",
                "ticker_data": {
                    "frequent_change": ["RISE"],
                    "average_price": [2.446000e06],
                    "total_trade_volume": [20.110270],
                },
            }
        }


class StockTsResp(BaseModel):
    next_average_price: List[float]

    class Config:
        schema_extra = {"example": {"next_average_price": [2441578.58370037]}}
