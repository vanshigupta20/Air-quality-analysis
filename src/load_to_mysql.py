"""Step 2: create the database/tables in MySQL and load the cleaned CSV.

Usage (from the project root):
    python -m src.load_to_mysql
"""
import pandas as pd

from src import config
from src.city_coords import CITY_COORDS
from src.clean_data import POLLUTANTS
from src.db import get_engine, run_sql_file


def main() -> None:
    if not config.CLEAN_CSV.exists():
        raise SystemExit("Cleaned file not found. Run:  python -m src.clean_data")

    # 1) Create the database + tables + view (DDL)
    server_engine = get_engine(with_database=False)
    run_sql_file(config.SQL_DIR / "01_schema.sql", server_engine)
    print("Database, tables and view created.")

    engine = get_engine()
    df = pd.read_csv(config.CLEAN_CSV, parse_dates=["date"])

    # 2) cities table
    cities = pd.DataFrame({"city_name": sorted(df["city"].unique())})
    cities["latitude"] = cities["city_name"].map(lambda c: CITY_COORDS.get(c, (None, None))[0])
    cities["longitude"] = cities["city_name"].map(lambda c: CITY_COORDS.get(c, (None, None))[1])
    cities.to_sql("cities", engine, if_exists="append", index=False)

    # 3) air_readings table (replace city name by city_id)
    id_map = pd.read_sql("SELECT city_id, city_name FROM cities", engine)
    readings = df.merge(id_map, left_on="city", right_on="city_name")
    readings = readings.rename(columns={"date": "reading_date"})
    readings["reading_date"] = readings["reading_date"].dt.date
    cols = ["city_id", "reading_date"] + POLLUTANTS + ["aqi", "aqi_bucket"]
    readings[cols].to_sql("air_readings", engine, if_exists="append", index=False,
                          chunksize=2000, method="multi")

    n_cities = pd.read_sql("SELECT COUNT(*) AS n FROM cities", engine)["n"][0]
    n_rows = pd.read_sql("SELECT COUNT(*) AS n FROM air_readings", engine)["n"][0]
    print(f"Loaded {n_cities} cities and {n_rows:,} readings into '{config.DB_NAME}'.")


if __name__ == "__main__":
    main()
