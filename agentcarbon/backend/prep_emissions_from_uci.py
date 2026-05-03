import pandas as pd
from pathlib import Path

RAW_PATH = Path("data/household_power_consumption.txt")
OUT_PATH = Path("data/emissions_history.csv")

EMISSION_FACTOR = 0.233  # kg CO2 per kWh (example UK grid)

def main():
    # 1. Load txt (semicolon-separated)
    df = pd.read_csv(
        RAW_PATH,
        sep=";",
        na_values=["?", "NA", ""],
        low_memory=False,
    )

    # 2. Keep only needed columns
    df = df[["Date", "Time", "Global_active_power"]]

    # 3. Parse datetime
    df["datetime"] = pd.to_datetime(
        df["Date"] + " " + df["Time"],
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce",
    )
    df = df.dropna(subset=["datetime", "Global_active_power"])

    # 4. Convert kW to kWh over time step
    # If data is 1-minute resolution: kWh = kW * (1/60); if hourly: kWh = kW * 1
    # UCI dataset is 1-minute; adjust if needed.
    df["kwh"] = df["Global_active_power"].astype(float) * (1.0 / 60.0)

    # 5. Aggregate to monthly totals
    df.set_index("datetime", inplace=True)
    monthly = df["kwh"].resample("M").sum().reset_index()

    monthly["date"] = monthly["datetime"].dt.date.astype(str)
    monthly["electricity_kwh"] = monthly["kwh"]

    # 6. Convert to emissions
    monthly["total_kgco2"] = monthly["electricity_kwh"] * EMISSION_FACTOR

    # 7. Dummy columns for gas & water (optional, set to 0 for now)
    monthly["gas_therms"] = 0.0
    monthly["water_gallons"] = 0.0

    out = monthly[["date", "total_kgco2", "electricity_kwh", "gas_therms", "water_gallons"]]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(out)} rows to {OUT_PATH}")

if __name__ == "__main__":
    main()
