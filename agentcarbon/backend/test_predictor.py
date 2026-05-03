from app.predictor import forecast_next_month

# Mock history (similar structure to what comes from DB)
mock_history = [
    {
        "fields": {
            "date": "2050-05-01",
            "energy_kwh": 250,
            "gas_therms": 118,
            "water_gallons": 440
        },
        "emissions": {
            "total_kgco2": 710
        }
    }
]

res = forecast_next_month(mock_history)
print("Prediction:", res)
