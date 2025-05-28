import requests
import pandas as pd
from datetime import datetime

# --- Config ---
LAT, LON = 51.96, 4.19
VARS = "temperature_2m,relative_humidity_2m,cloud_cover,direct_radiation,dew_point_2m,surface_pressure,wind_speed_10m,vapour_pressure_deficit,diffuse_radiation,shortwave_radiation"
FORECAST_DAYS = 2  # Can be up to 16
URL = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly={VARS}&forecast_days={FORECAST_DAYS}&timezone=auto"

# --- Fetch ---
response = requests.get(URL)
data = response.json()

# --- Parse hourly data ---
df = pd.DataFrame(data['hourly'])

# --- Save to CSV or Excel ---
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
df.to_excel(f"weather_forecast_{timestamp}.xlsx", index=False)
print("✅ Forecast saved!")
