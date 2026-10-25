"""Central place for paths and database settings (read from the .env file)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

RAW_CSV = ROOT / "data" / "raw" / "city_day.csv"
CLEAN_CSV = ROOT / "data" / "processed" / "city_day_clean.csv"
SQL_DIR = ROOT / "sql"

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "air_quality_db")
