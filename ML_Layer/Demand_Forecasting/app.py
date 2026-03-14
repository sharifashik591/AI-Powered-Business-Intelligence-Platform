# Update: Delete old forecast rows first, then insert new forecast rows (every API hit)
# This version:
# 1) Loads history from Postgres
# 2) Generates next N-day forecast
# 3) DELETEs all old rows from analytics.demand_forecast_15d
# 4) INSERTs fresh forecast rows
#
# pip install flask pandas numpy scikit-learn joblib sqlalchemy python-dotenv psycopg2-binary

import os
import joblib
import pandas as pd
import numpy as np
from flask import Flask, jsonify, request
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# -----------------------
# Load env
# -----------------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "saved_model", "best_model.pkl")
MODEL_NAME = "best_5_models_v1"

# Your history source (must have: date, category, region, quantity)
HISTORY_TABLE = "analytics.ml_daily_demand_category_region"  # <-- change this to your real table/view

# Where forecasts are stored
FORECAST_SCHEMA = "analytics"
FORECAST_TABLE = "demand_forecast_15d"  # full name => analytics.demand_forecast_15d


def get_db_engine():
    connection_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(connection_url, pool_pre_ping=True)


engine = get_db_engine()
model = joblib.load(MODEL_PATH)

app = Flask(__name__)


# -----------------------
# Feature function (same as training)
# -----------------------
def make_features(data: pd.DataFrame) -> pd.DataFrame:
    d = data.sort_values(["category", "region", "date"]).copy()

    d["dow"] = d["date"].dt.dayofweek
    d["month"] = d["date"].dt.month
    d["is_weekend"] = (d["dow"] >= 5).astype(int)

    g = d.groupby(["category", "region"], sort=False)
    d["lag_1"] = g["quantity"].shift(1)
    d["lag_7"] = g["quantity"].shift(7)
    d["lag_14"] = g["quantity"].shift(14)
    d["rollmean_7"] = g["quantity"].shift(1).rolling(7).mean()

    return d


# -----------------------
# Pull history from PGSQL
# -----------------------
def load_history_from_db(days_back: int = 365) -> pd.DataFrame:
    q = f"""
        SELECT 
            d.full_date AS date, 
            p.category,
            c.region,                
            SUM(f.quantity) AS quantity
        FROM warehouse.fact_sales f
        JOIN warehouse.dim_date d ON f.date_id = d.date_id        
        JOIN warehouse.dim_customer c ON f.customer_id = c.customer_id 
        JOIN warehouse.dim_product p ON f.product_id = p.product_id
        WHERE d.full_date >= (CURRENT_DATE - INTERVAL '{days_back} days')
        GROUP BY d.full_date, p.category, c.region
        ORDER BY p.category, c.region, d.full_date;
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(q), conn)

    df["date"] = pd.to_datetime(df["date"])
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0.0)
    df["category"] = df["category"].astype(str)
    df["region"] = df["region"].astype(str)

    return df


# -----------------------
# Forecast next N days (recursive)
# -----------------------
def forecast_recursive(df: pd.DataFrame, horizon: int = 15) -> pd.DataFrame:
    df = df.sort_values(["category", "region", "date"]).reset_index(drop=True)
    last_date = df["date"].max()
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon, freq="D")

    forecasts = []

    for (cat, reg), g in df.groupby(["category", "region"], sort=False):
        g = g.sort_values("date").copy()

        for d in future_dates:
            g = pd.concat([g, pd.DataFrame([{
                "date": d, "category": cat, "region": reg, "quantity": np.nan
            }])], ignore_index=True)

            gg = make_features(g)
            row = gg.iloc[-1]

            if pd.isna(row["lag_14"]) or pd.isna(row["rollmean_7"]):
                yhat = 0.0
            else:
                X_row = pd.DataFrame([{
                    "category": cat,
                    "region": reg,
                    "dow": int(row["dow"]),
                    "month": int(row["month"]),
                    "is_weekend": int(row["is_weekend"]),
                    "lag_1": float(row["lag_1"]),
                    "lag_7": float(row["lag_7"]),
                    "lag_14": float(row["lag_14"]),
                    "rollmean_7": float(row["rollmean_7"]),
                }])

                yhat = float(model.predict(X_row)[0])
                yhat = max(0.0, yhat)

            g.loc[g.index[-1], "quantity"] = yhat

            forecasts.append({
                "forecast_date": d.date(),
                "category": cat,
                "region": reg,
                "predicted_quantity": yhat
            })

    return pd.DataFrame(forecasts)


# -----------------------
# DELETE ALL OLD + INSERT NEW
# -----------------------
def replace_forecast_table(forecast_df: pd.DataFrame):
    """
    Transaction:
      1) DELETE all existing rows
      2) INSERT new forecast rows
    """
    out = forecast_df.copy()
    out["model_name"] = MODEL_NAME

    with engine.begin() as conn:
        # Delete all old forecast rows
        conn.execute(text(f"DELETE FROM {FORECAST_SCHEMA}.{FORECAST_TABLE};"))

        # Insert new rows (append)
        out.to_sql(
            name=FORECAST_TABLE,
            con=conn,
            schema=FORECAST_SCHEMA,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=5000
        )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/forecast", methods=["GET"])
def forecast():
    """
    Example:
    http://127.0.0.1:5000/forecast?horizon=15&days_back=365
    """

    horizon = int(request.args.get("horizon", 15))
    days_back = int(request.args.get("days_back", 365))

    history_df = load_history_from_db(days_back=days_back)
    if history_df.empty:
        return jsonify({"error": "No history data found in DB."}), 400

    forecast_df = forecast_recursive(history_df, horizon=horizon)

    # Delete old forecast and insert new one
    replace_forecast_table(forecast_df)

    return jsonify({
        "status": "success",
        "horizon": horizon,
        "saved_rows": len(forecast_df)
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)