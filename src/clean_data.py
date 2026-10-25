"""Step 1: clean the raw Kaggle file.

Usage (from the project root):
    python -m src.clean_data
    python -m src.clean_data --file data/sample/city_day_sample.csv
"""
import argparse

import numpy as np
import pandas as pd

from src import config

COLUMN_MAP = {
    "City": "city", "Date": "date",
    "PM2.5": "pm25", "PM10": "pm10", "NO": "no_gas", "NO2": "no2", "NOx": "nox",
    "NH3": "nh3", "CO": "co", "SO2": "so2", "O3": "o3",
    "Benzene": "benzene", "Toluene": "toluene", "Xylene": "xylene",
    "AQI": "aqi", "AQI_Bucket": "aqi_bucket",
}
POLLUTANTS = ["pm25", "pm10", "no_gas", "no2", "nox", "nh3", "co", "so2",
              "o3", "benzene", "toluene", "xylene"]


def aqi_to_bucket(aqi: float) -> str:
    """CPCB AQI categories."""
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Satisfactory"
    if aqi <= 200:
        return "Moderate"
    if aqi <= 300:
        return "Poor"
    if aqi <= 400:
        return "Very Poor"
    return "Severe"


def clean(raw_path) -> tuple[pd.DataFrame, list[str]]:
    report = []
    df = pd.read_csv(raw_path)
    report.append(f"Raw rows: {len(df):,}   Cities: {df['City'].nunique()}")

    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    report.append("Missing values in raw data:")
    for col, n in missing.items():
        report.append(f"  {col:<12} {n:>6,}  ({n / len(df) * 100:.1f} percent)")

    df = df.rename(columns=COLUMN_MAP)
    df["city"] = df["city"].str.strip()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["date"])
    report.append(f"Dropped {before - len(df):,} rows with an invalid date")

    before = len(df)
    df = df.drop_duplicates(subset=["city", "date"])
    report.append(f"Dropped {before - len(df):,} duplicate city-date rows")

    # Negative concentrations are sensor errors -> treat as missing
    for col in POLLUTANTS + ["aqi"]:
        df.loc[df[col] < 0, col] = np.nan

    # AQI is the key measure of this project, so rows without it are dropped.
    # Pollutant columns are NOT imputed: they stay NULL and are ignored by AVG().
    before = len(df)
    df = df.dropna(subset=["aqi"])
    report.append(f"Dropped {before - len(df):,} rows with missing AQI")

    # Rebuild the bucket from the AQI value so it is always consistent
    df["aqi_bucket"] = df["aqi"].apply(aqi_to_bucket)

    df = df.sort_values(["city", "date"]).reset_index(drop=True)
    report.append(f"Clean rows: {len(df):,}   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    return df, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=str(config.RAW_CSV), help="path to the raw city_day.csv")
    args = parser.parse_args()

    df, report = clean(args.file)
    config.CLEAN_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.CLEAN_CSV, index=False)
    print("\n".join(report))
    print(f"\nSaved cleaned file to {config.CLEAN_CSV}")


if __name__ == "__main__":
    main()
