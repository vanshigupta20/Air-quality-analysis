"""Quick check that Python can talk to MySQL.   python -m src.test_connection"""
from sqlalchemy import text

from src import config
from src.db import get_engine

try:
    with get_engine(with_database=False).connect() as conn:
        version = conn.execute(text("SELECT VERSION()")).scalar()
    print(f"Connected to MySQL {version} at {config.DB_HOST}:{config.DB_PORT} as '{config.DB_USER}'")
except Exception as exc:  # noqa: BLE001
    print("Connection FAILED:", exc)
    print("Check: MySQL80 service running? Correct password in .env? Port 3306?")
