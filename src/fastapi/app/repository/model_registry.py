from dataclasses import asdict

import mlflow
from app.common.config import Config

conf_dict = asdict(Config())
mlflow.set_tracking_uri(conf_dict["MLFLOW_URI"])


def load_rf_model(name: str):
    model = mlflow.sklearn.load_model(f"models:/{name}/Production")

    return model
