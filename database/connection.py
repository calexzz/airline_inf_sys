"""
Подключение к SQLite. Создаёт таблицы и загружает CSV при первом запуске.
"""

import sqlite3
from pathlib import Path

# Пути
_BASE_DIR = Path(__file__).parent
_DB_PATH = _BASE_DIR / "airline.db"
_SCHEMA_SQL = _BASE_DIR / "schema.sql"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()

    schema = _SCHEMA_SQL.read_text(encoding="utf-8")
    conn.executescript(schema)

    from database.seed_loader import seed
    seed(conn)

    conn.close()
    print(f"init_db: БД готова → {_DB_PATH}")
