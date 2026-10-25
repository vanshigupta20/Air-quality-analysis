"""Creates a SYNTHETIC file in the same format as the Kaggle city_day.csv.

It exists only so you can test the whole pipeline (MySQL + Streamlit) before
downloading the real data. NEVER use these numbers in your report.

    python -m src.make_sample_data
"""
import numpy as np
import pandas as pd

from src import config
from src.city_coords import CITY_COORDS

rng = np.random.default_rng(42)
OUT = config.ROOT / "data" / "sample" / "city_day_sample.csv"

# rough "pollution level" per city so the charts look plausible
BASE = {c: 90 for c in CITY_COORDS}
BASE.update({"Delhi": 180, "Patna": 170, "Gurugram": 150, "Lucknow": 150, "Ahmedabad": 140,
             "Kolkata": 110, "Jaipur": 100, "Amritsar": 105, "Mumbai": 85,
             "Kochi": 50, "Thiruvananthapuram": 50, "Aizawl": 40, "Shillong": 45,
             "Ernakulam": 55, "Bengaluru": 65, "Chennai": 70, "Visakhapatnam": 85})
SEASON_FACTOR = {12: 1.5, 1: 1.6, 2: 1.3, 3: 1.0, 4: 0.9, 5: 0.9,
                 6: 0.6, 7: 0.45, 8: 0.45, 9: 0.6, 10: 1.25, 11: 1.5}


def bucket(a):
    return ("Good" if a <= 50 else "Satisfactory" if a <= 100 else "Moderate" if a <= 200
            else "Poor" if a <= 300 else "Very Poor" if a <= 400 else "Severe")


rows = []
for city in CITY_COORDS:
    start = pd.Timestamp("2015-01-01") + pd.Timedelta(days=int(rng.integers(0, 900)))
    dates = pd.date_range(start, "2020-07-01")
    for d in dates:
        level = BASE[city] * SEASON_FACTOR[d.month] * rng.lognormal(0, 0.28)
        if pd.Timestamp("2020-03-25") <= d <= pd.Timestamp("2020-04-30"):
            level *= 0.55  # imitate the lockdown dip
        aqi = float(np.clip(level, 15, 500))
        pm25 = aqi * rng.uniform(0.45, 0.6)
        rows.append({
            "City": city, "Date": d.strftime("%Y-%m-%d"),
            "PM2.5": pm25, "PM10": pm25 * rng.uniform(1.6, 2.2),
            "NO": rng.uniform(5, 40), "NO2": rng.uniform(10, 60), "NOx": rng.uniform(15, 80),
            "NH3": rng.uniform(5, 40), "CO": rng.uniform(0.3, 3.0), "SO2": rng.uniform(4, 30),
            "O3": rng.uniform(10, 80), "Benzene": rng.uniform(0, 6),
            "Toluene": rng.uniform(0, 15), "Xylene": rng.uniform(0, 5),
            "AQI": aqi, "AQI_Bucket": bucket(aqi),
        })

df = pd.DataFrame(rows).round(2)
# imitate the real file's problems: many missing values
for col in ["PM2.5", "PM10", "NO", "NO2", "NOx", "NH3", "CO", "SO2", "O3", "Benzene", "Toluene", "Xylene"]:
    df.loc[df.sample(frac=rng.uniform(0.05, 0.35), random_state=int(rng.integers(1e6))).index, col] = np.nan
df.loc[df.sample(frac=0.12, random_state=1).index, ["AQI", "AQI_Bucket"]] = np.nan
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"Wrote {len(df):,} SYNTHETIC rows to {OUT}")
