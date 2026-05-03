EMISSION_FACTORS = {
    "electricity_kwh": 0.233,   # kg CO2 / kWh (example, UK grid)
    "natural_gas_therm": 5.3,   # kg CO2 / therm (approx)
    "water_gallon": 0.0003,     # optional, process-related
}

def compute_emissions(fields: dict) -> dict:
    emissions = {"items": []}

    kwh = fields.get("energy_kwh")
    if kwh is not None:
        e = kwh * EMISSION_FACTORS["electricity_kwh"]
        emissions["items"].append({"type": "electricity", "quantity": kwh, "unit": "kWh", "kgco2": e})

    liters = fields.get("fuel_liters")
    if liters is not None:
        # add when you have fuel data
        pass

    gas_therms = fields.get("gas_therms")
    if gas_therms is not None:
        e = gas_therms * EMISSION_FACTORS["natural_gas_therm"]
        emissions["items"].append({"type": "gas", "quantity": gas_therms, "unit": "therms", "kgco2": e})

    water_gal = fields.get("water_gallons")
    if water_gal is not None:
        e = water_gal * EMISSION_FACTORS["water_gallon"]
        emissions["items"].append({"type": "water", "quantity": water_gal, "unit": "gallons", "kgco2": e})

    emissions["total_kgco2"] = round(sum(i["kgco2"] for i in emissions["items"]), 3)
    return emissions
