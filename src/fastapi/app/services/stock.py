from typing import Dict

import numpy as np
import pandas as pd
from app.repository.model_registry import load_rf_model


def predict_stock(model_name: str, ts: Dict) -> float:
    # Load Model (Maybe Caching)
    model = load_rf_model(model_name)

    # Preprocessing
    df = pd.DataFrame(ts)
    df["frequent_change"] = df["frequent_change"].apply(
        lambda x: 1 if x == "RISE" else 0
    )

    # Create Result
    pred_result = model.predict(df).tolist()

    return pred_result
