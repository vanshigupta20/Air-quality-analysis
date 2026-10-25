"""Database helpers: build the SQLAlchemy engine, run .sql files, parse the queries file."""
import re
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from src import config


def get_engine(with_database: bool = True):
    """Return a SQLAlchemy engine for MySQL.

    URL.create() is used (instead of an f-string) so passwords that contain
    characters like @ # / : still work.
    """
    url = URL.create(
        drivername="mysql+pymysql",
        username=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME if with_database else None,
    )
    return create_engine(url, pool_pre_ping=True)


def run_sql_file(path: Path, engine) -> None:
    """Execute every statement of a .sql file (statements are separated by ';').

    Note: keep % signs out of the .sql files that are run this way.
    """
    lines = [ln for ln in Path(path).read_text(encoding="utf-8").splitlines()
             if not ln.strip().startswith("--")]
    statements = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            conn.exec_driver_sql(stmt)


def load_named_queries(path: Path) -> list[dict]:
    """Parse sql/02_queries.sql into [{name, title, concept, sql}, ...]."""
    queries, current = [], None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"--\s*(name|title|concept):\s*(.+)", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            if key == "name":
                current = {"name": value, "title": value, "concept": "", "sql": ""}
                queries.append(current)
            elif current is not None:
                current[key] = value
        elif current is not None and not line.strip().startswith("--"):
            current["sql"] += line + "\n"
    for q in queries:
        q["sql"] = q["sql"].strip().rstrip(";").strip()
    return queries
