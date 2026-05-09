"""
Читает CSV-файлы из папки data/ и загружает данные в SQLite.
Вызывается один раз при первом запуске (если таблицы пустые).
"""

import csv
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

def _load_airports(conn: sqlite3.Connection) -> None:
    with open(DATA_DIR / "airports.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    conn.executemany(
        """INSERT OR IGNORE INTO airports (iata_code, name, city, country)
           VALUES (:iata_code, :name, :city, :country)""",
        rows,
    )

def _load_aircrafts(conn: sqlite3.Connection) -> None:
    with open(DATA_DIR / "aircrafts.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    conn.executemany(
        """INSERT OR IGNORE INTO aircrafts (reg_number, model, capacity, status)
           VALUES (:reg_number, :model, :capacity, :status)""",
        rows,
    )

def _load_flights(conn: sqlite3.Connection) -> None:
    """
    В CSV хранятся IATA-код аэропорта и рег. номер ВС (читаемо!),
    но в БД нужны числовые id — делаем lookup.
    """
    with open(DATA_DIR / "flights.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Строим словари для подстановки
    airport_id = {
        row[0]: row[1]
        for row in conn.execute("SELECT iata_code, airport_id FROM airports")
    }
    aircraft_id = {
        row[0]: row[1]
        for row in conn.execute("SELECT reg_number, aircraft_id FROM aircrafts")
    }

    prepared = []
    for r in rows:
        prepared.append({
            "flight_number":  r["flight_number"],
            "origin_id":      airport_id[r["origin_iata"]],
            "dest_id":        airport_id[r["dest_iata"]],
            "aircraft_id":    aircraft_id[r["aircraft_reg"]],
            "departure_time": r["departure_time"],
            "arrival_time":   r["arrival_time"],
            "base_price":     float(r["base_price"]),
            "status":         r["status"],
        })

    conn.executemany(
        """INSERT OR IGNORE INTO flights
           (flight_number, origin_id, dest_id, aircraft_id,
            departure_time, arrival_time, base_price, status)
           VALUES (:flight_number, :origin_id, :dest_id, :aircraft_id,
                   :departure_time, :arrival_time, :base_price, :status)""",
        prepared,
    )

def _load_passengers(conn: sqlite3.Connection) -> None:
    with open(DATA_DIR / "passengers.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    conn.executemany(
        """INSERT OR IGNORE INTO passengers
           (last_name, first_name, passport_num, email, phone)
           VALUES (:last_name, :first_name, :passport_num, :email, :phone)""",
        rows,
    )

def _load_bookings(conn: sqlite3.Connection) -> None:
    with open(DATA_DIR / "bookings.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    passenger_id = {
        row[0]: row[1]
        for row in conn.execute("SELECT passport_num, passenger_id FROM passengers")
    }
    flight_id = {
        row[0]: row[1]
        for row in conn.execute("SELECT flight_number, flight_id FROM flights")
    }

    prepared = []
    for r in rows:
        prepared.append({
            "passenger_id": passenger_id[r["passenger_passport"]],
            "flight_id":    flight_id[r["flight_number"]],
            "seat_number":  r["seat_number"],
            "class":        r["class"],
            "price":        float(r["price"]),
            "status":       r["status"],
            "booked_at":    r["booked_at"],
        })

    conn.executemany(
        """INSERT OR IGNORE INTO bookings
           (passenger_id, flight_id, seat_number, class, price, status, booked_at)
           VALUES (:passenger_id, :flight_id, :seat_number, :class,
                   :price, :status, :booked_at)""",
        prepared,
    )

def _load_crew_members(conn: sqlite3.Connection) -> None:
    with open(DATA_DIR / "crew_members.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    conn.executemany(
        """INSERT OR IGNORE INTO crew_members
           (last_name, first_name, role, license_num, license_exp)
           VALUES (:last_name, :first_name, :role, :license_num, :license_exp)""",
        rows,
    )

def _load_flight_crew(conn: sqlite3.Connection) -> None:
    with open(DATA_DIR / "flight_crew.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    flight_id = {
        row[0]: row[1]
        for row in conn.execute("SELECT flight_number, flight_id FROM flights")
    }
    crew_id = {
        row[0]: row[1]
        for row in conn.execute("SELECT license_num, crew_id FROM crew_members")
    }

    prepared = []
    for r in rows:
        prepared.append({
            "flight_id": flight_id[r["flight_number"]],
            "crew_id":   crew_id[r["crew_license"]],
            "position":  r["position"],
        })

    conn.executemany(
        """INSERT OR IGNORE INTO flight_crew (flight_id, crew_id, position)
           VALUES (:flight_id, :crew_id, :position)""",
        prepared,
    )

def seed(conn: sqlite3.Connection) -> None:
    """
    Загружает все CSV в БД
    """
    count = conn.execute("SELECT COUNT(*) FROM airports").fetchone()[0]
    if count > 0:
        print("seed: данные уже загружены, пропускаем.")
        return

    print("seed: загружаем данные из CSV...")
    _load_airports(conn)
    _load_aircrafts(conn)
    _load_flights(conn)
    _load_passengers(conn)
    _load_bookings(conn)
    _load_crew_members(conn)
    _load_flight_crew(conn)
    conn.commit()
    print("seed: готово")
