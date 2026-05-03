import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import joblib
from pathlib import Path

# Paths
DATA_PATH = Path("data/emissions_history.csv")
MODEL_PATH = Path("data/predictor_model.pkl")

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure date is datetime
    df["date"] = pd.to_datetime(df["date"])
    
    # Extract simple time features
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year
    
    # Simple seasonal flags
    df["is_winter"] = df["month"].isin([12, 1, 2]).astype(int)
    df["is_summer"] = df["month"].isin([4, 5, 6]).astype(int)
    return df

def main():
    if not DATA_PATH.exists():
        print(f"Error: {DATA_PATH} not found. Run prep_emissions_from_uci.py first.")
        return

    # 1. Load data
    df = pd.read_csv(DATA_PATH)
    df = add_time_features(df)

    # 2. Define features & target
    feature_cols = [
        "electricity_kwh",
        "gas_therms",
        "water_gallons",
        "month",
        "year",
        "is_winter",
        "is_summer",
    ]
    target_col = "total_kgco2"

    # Drop rows with missing values if any
    df = df.dropna(subset=feature_cols + [target_col])

    X = df[feature_cols]
    y = df[target_col]

    # 3. Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 4. Train Random Forest
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)


    

    # 5. Evaluate
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    print(f"[SUCCESS] Training complete.")
    print(f"MAE:  {mae:.4f} kg CO2")
    print(f"RMSE: {rmse:.4f} kg CO2")
    print(f"R2:   {r2:.4f} (1.0 = perfect)")




    # 6. Save model
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "feature_cols": feature_cols}, MODEL_PATH)
    print(f"[SAVED] Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    main()
