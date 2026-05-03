import joblib
from typing import List, Dict
import pandas as pd
from prophet import Prophet
from pathlib import Path
import warnings
from datetime import datetime


# Path to the model you trained in train_predictor.py
MODEL_PATH = Path("data/predictor_model.pkl")


def predict_usage_impact(kwh: float, gas: float, water: float, date_str: str):
    """
    Uses the TRAINED Random Forest model to predict CO2 based on consumption.
    This is your 'Usage Intelligence'.
    """
    if not MODEL_PATH.exists():
        return None

    try:
        # Load the saved model and features
        saved_data = joblib.load(MODEL_PATH)
        model = saved_data["model"]
        feature_cols = saved_data["feature_cols"]

        # Prepare features
        dt = pd.to_datetime(date_str)
        month = dt.month
        year = dt.year
        
        # Create input row matching the training format
        input_df = pd.DataFrame([{
            "electricity_kwh": kwh,
            "gas_therms": gas,
            "water_gallons": water,
            "month": month,
            "year": year,
            "is_winter": 1 if month in [12, 1, 2] else 0,
            "is_summer": 1 if month in [4, 5, 6] else 0
        }])

        prediction = model.predict(input_df[feature_cols])
        return round(float(prediction[0]), 2)
    except Exception as e:
        print(f"ML Prediction Error: {e}")
        return None


def forecast_next_month(history: List[Dict]) -> Dict:
    """
    Uses PROPHET to forecast next month based on history.
    This is your 'Time-Series Forecasting'.
    """
    rows = []
    if not history:
        return {"predicted_kgco2": None}
        
    for h in history:
        date = h.get("date")
        total = h.get("total_kgco2")
        
        # Skip if missing data
        if not date or total is None:
            continue
        
        try:
            total_float = float(total)
        except (ValueError, TypeError):
            continue
            
        # Try to parse date - handle various formats
        parsed_date = None
        try:
            if isinstance(date, str):
                # Try common date formats (including formats like "01-Jan-2025", "01-Mar-2025")
                date_formats = [
                    "%Y-%m-%d", 
                    "%Y/%m/%d", 
                    "%m/%d/%Y", 
                    "%d/%m/%Y", 
                    "%Y-%m-%dT%H:%M:%S",
                    "%d-%b-%Y",  # e.g., "01-Jan-2025"
                    "%d-%B-%Y",  # e.g., "01-January-2025"
                    "%d-%m-%Y",  # e.g., "01-01-2025"
                    "%b %d, %Y",  # e.g., "Jan 01, 2025"
                    "%B %d, %Y",  # e.g., "January 01, 2025"
                ]
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(date, fmt)
                        break
                    except ValueError:
                        continue
            elif isinstance(date, datetime):
                parsed_date = date
            
            if parsed_date:
                rows.append({"ds": parsed_date, "y": total_float})
        except (ValueError, TypeError, AttributeError) as e:
            # Skip entries with unparseable dates
            continue
    
    # Need at least 3 data points for Prophet
    if len(rows) < 3:
        return {"predicted_kgco2": None}

    try:
        df = pd.DataFrame(rows)
        df = df.sort_values("ds")  # Prophet requires sorted dates
        
        # Suppress Prophet warnings for cleaner logs
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            
            m = Prophet()
            m.fit(df)
            # Use 'ME' instead of deprecated 'M' for monthly frequency
            future = m.make_future_dataframe(periods=1, freq="ME")
            fcst = m.predict(future)
            pred = float(fcst.iloc[-1]["yhat"])
            
            # Ensure prediction is non-negative
            pred = max(0, pred)
            
        return {"predicted_kgco2": round(pred, 2)}
    except Exception as e:
        # Log error for debugging but return None
        import logging
        logging.error(f"Forecast error: {str(e)}")
        return {"predicted_kgco2": None}
