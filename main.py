import requests
import pandas as pd
import matplotlib.pyplot as plt

# User-defined parameters
LAT, LON = 57.02546575887769, 9.951696793042322  # Example: Aalborg
YEARLY_HEATING_KWH = 18100   # Your total district heating usage in kWh
BASE_TEMPERATURE = 15.0      # HDD base temperature (commonly 18°C). This is when you stop heating.
YEAR = 2022                 # Year for which to estimate heating usage
START = "2022-11-01"         # Start date for historical data
END = "2023-10-31"           # End date for historical data
WARM_WATER_USAGE_DAY_KWH = 2.5 # Warm water usage per day in kWh (approximate value for 50L/day)

# convert start and end to datetimes
START_DT = pd.to_datetime(START)
END_DT = pd.to_datetime(END)

# subtract timerange warm water usage from total yearly heating usage
timerange = END_DT - START_DT
YEARLY_HEATING_KWH -= timerange.days * WARM_WATER_USAGE_DAY_KWH
print(f"Adjusted yearly heating usage: {YEARLY_HEATING_KWH} kWh (excluding warm water estimated at {timerange.days * WARM_WATER_USAGE_DAY_KWH} kWh/year)")


# Fetch historical temperature data from Open-Meteo
def get_weather_data(lat, lon, year):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START,
        "end_date": END,
        "daily": ["apparent_temperature_max", "apparent_temperature_min"],
        "timezone": "auto"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return pd.DataFrame({
        "date": pd.to_datetime(data["daily"]["time"]),
        "temp_min": data["daily"]["apparent_temperature_min"],
        "temp_max": data["daily"]["apparent_temperature_max"]
    })

# Calculate HDD and distribute heating usage
def compute_heating_demand(df, yearly_kwh, base_temp):
    df["temp_avg"] = (df["temp_min"] + df["temp_max"]) / 2
    df["HDD"] = (base_temp - df["temp_avg"]).clip(lower=0)
    total_HDD = df["HDD"].sum()
    df["estimated_usage_kWh"] = (df["HDD"] / total_HDD) * yearly_kwh  # Proportional allocation
    return df

# Fetch, process, and plot
df = get_weather_data(LAT, LON, YEAR)
df = compute_heating_demand(df, YEARLY_HEATING_KWH, BASE_TEMPERATURE)

# Plot the estimated daily heating usage
plt.figure(figsize=(12, 5))
plt.plot(df["date"], df["estimated_usage_kWh"], label="Estimated Daily Heating Usage (kWh)", color="red")
plt.xlabel("Date")
plt.ylabel("kWh")
plt.title(f"Estimated Daily Heating ({YEAR}) @ {YEARLY_HEATING_KWH} kWh, base TDD {BASE_TEMPERATURE} C (warm water est. {timerange.days * WARM_WATER_USAGE_DAY_KWH} kWh excluded)")
plt.legend()
plt.grid()
plt.show()
