import uvicorn

from app.routes.api import router
from starlette.middleware.cors import CORSMiddleware

from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(version="1.0.0", title="StockPricePrediction")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


if __name__ == "__main__":
    app = create_app()

    uvicorn.run(app, host="0.0.0.0", port=8000)
