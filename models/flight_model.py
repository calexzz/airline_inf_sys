import sqlite3
from database.connection import get_connection

def get_all_flights() -> list[sqlite3.Row]:
    """Все рейсы с названиями аэропортов и моделью ВС"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            f.flight_id,
            f.flight_number,
            a1.city        AS origin_city,
            a1.iata_code   AS origin_iata,
            a2.city        AS dest_city,
            a2.iata_code   AS dest_iata,
            ac.model       AS aircraft_model,
            ac.reg_number  AS aircraft_reg,
            f.departure_time,
            f.arrival_time,
            f.base_price,
            f.status
        FROM flights f
        JOIN airports a1  ON f.origin_id   = a1.airport_id
        JOIN airports a2  ON f.dest_id     = a2.airport_id
        JOIN aircrafts ac ON f.aircraft_id = ac.aircraft_id
        ORDER BY f.departure_time
    """).fetchall()
    conn.close()
    return rows


def get_flight_by_id(flight_id: int) -> sqlite3.Row | None:
    """Один рейс по flight_id"""
    conn = get_connection()
    row = conn.execute("""
        SELECT
            f.flight_id,
            f.flight_number,
            a1.city        AS origin_city,
            a1.iata_code   AS origin_iata,
            a2.city        AS dest_city,
            a2.iata_code   AS dest_iata,
            ac.model       AS aircraft_model,
            ac.reg_number  AS aircraft_reg,
            f.departure_time,
            f.arrival_time,
            f.base_price,
            f.status
        FROM flights f
        JOIN airports a1  ON f.origin_id   = a1.airport_id
        JOIN airports a2  ON f.dest_id     = a2.airport_id
        JOIN aircrafts ac ON f.aircraft_id = ac.aircraft_id
        WHERE f.flight_id = ?
    """, (flight_id,)).fetchone()
    conn.close()
    return row


def get_flights_by_route(origin_iata: str, dest_iata: str) -> list[sqlite3.Row]:
    """Рейсы по маршруту, например: SVO - LED"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            f.flight_id,
            f.flight_number,
            a1.city        AS origin_city,
            a2.city        AS dest_city,
            f.departure_time,
            f.arrival_time,
            f.base_price,
            f.status
        FROM flights f
        JOIN airports a1  ON f.origin_id = a1.airport_id
        JOIN airports a2  ON f.dest_id   = a2.airport_id
        WHERE a1.iata_code = ? AND a2.iata_code = ?
        ORDER BY f.departure_time
    """, (origin_iata, dest_iata)).fetchall()
    conn.close()
    return rows


def search_flights(query: str) -> list[sqlite3.Row]:
    like = f"%{query}%"
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            f.flight_id,
            f.flight_number,
            a1.city       AS origin_city,
            a1.iata_code  AS origin_iata,
            a2.city       AS dest_city,
            a2.iata_code  AS dest_iata,
            ac.model      AS aircraft_model,
            ac.reg_number AS aircraft_reg,
            f.departure_time,
            f.arrival_time,
            f.base_price,
            f.status
        FROM flights f
        JOIN airports a1  ON f.origin_id   = a1.airport_id
        JOIN airports a2  ON f.dest_id     = a2.airport_id
        JOIN aircrafts ac ON f.aircraft_id = ac.aircraft_id
        WHERE f.flight_number LIKE ?
           OR a1.city         LIKE ?
           OR a2.city         LIKE ?
        ORDER BY f.departure_time
    """, (like, like, like)).fetchall()
    conn.close()
    return rows


def get_flight_load(flight_id: int) -> sqlite3.Row | None:
    """
    Загрузка рейса: сколько мест продано и сколько всего.
    Возвращает: flight_number, capacity, sold, free, load_pct
    """
    conn = get_connection()
    row = conn.execute("""
        SELECT
            f.flight_number,
            ac.capacity,
            COUNT(b.booking_id)                                    AS sold,
            ac.capacity - COUNT(b.booking_id)                      AS free,
            ROUND(100.0 * COUNT(b.booking_id) / ac.capacity, 1)   AS load_pct
        FROM flights f
        JOIN aircrafts ac ON f.aircraft_id = ac.aircraft_id
        LEFT JOIN bookings b
               ON b.flight_id = f.flight_id AND b.status = 'confirmed'
        WHERE f.flight_id = ?
        GROUP BY f.flight_id
    """, (flight_id,)).fetchone()
    conn.close()
    return row

def add_flight(
    flight_number: str,
    origin_iata: str,
    dest_iata: str,
    aircraft_reg: str,
    departure_time: str,
    arrival_time: str,
    base_price: float,
    status: str = "scheduled",
) -> int:
    """
    Добавляет новый рейс. Возвращает flight_id новой записи.
    """
    conn = get_connection()

    origin_id = conn.execute(
        "SELECT airport_id FROM airports WHERE iata_code = ?", (origin_iata,)
    ).fetchone()
    dest_id = conn.execute(
        "SELECT airport_id FROM airports WHERE iata_code = ?", (dest_iata,)
    ).fetchone()
    aircraft_id = conn.execute(
        "SELECT aircraft_id FROM aircrafts WHERE reg_number = ?", (aircraft_reg,)
    ).fetchone()

    if not origin_id:
        raise ValueError(f"Аэропорт не найден: {origin_iata}")
    if not dest_id:
        raise ValueError(f"Аэропорт не найден: {dest_iata}")
    if not aircraft_id:
        raise ValueError(f"Воздушное судно не найдено: {aircraft_reg}")

    cur = conn.execute("""
        INSERT INTO flights
            (flight_number, origin_id, dest_id, aircraft_id,
             departure_time, arrival_time, base_price, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        flight_number,
        origin_id["airport_id"],
        dest_id["airport_id"],
        aircraft_id["aircraft_id"],
        departure_time,
        arrival_time,
        base_price,
        status,
    ))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id

def update_flight(
    flight_id: int,
    departure_time: str,
    arrival_time: str,
    base_price: float,
    status: str,
) -> None:
    """Обновляет время вылета/прилёта, цену и статус рейса"""
    conn = get_connection()
    conn.execute("""
        UPDATE flights
        SET departure_time = ?,
            arrival_time   = ?,
            base_price     = ?,
            status         = ?
        WHERE flight_id = ?
    """, (departure_time, arrival_time, base_price, status, flight_id))
    conn.commit()
    conn.close()


def update_flight_status(flight_id: int, status: str) -> None:
    """Быстрая смена статуса: scheduled / departed / arrived / cancelled"""
    allowed = {"scheduled", "departed", "arrived", "cancelled"}
    if status not in allowed:
        raise ValueError(f"Недопустимый статус: {status}. Допустимые: {allowed}")

    conn = get_connection()
    conn.execute(
        "UPDATE flights SET status = ? WHERE flight_id = ?",
        (status, flight_id)
    )
    conn.commit()
    conn.close()

def delete_flight(flight_id: int) -> None:
    """
    Удаляет рейс. Сначала проверяет нет ли подтверждённых бронирований.
    Если есть - выбрасывает исключение (нельзя удалить рейс с пассажирами)
    """
    conn = get_connection()

    confirmed = conn.execute("""
        SELECT COUNT(*) FROM bookings
        WHERE flight_id = ? AND status = 'confirmed'
    """, (flight_id,)).fetchone()[0]

    if confirmed > 0:
        conn.close()
        raise ValueError(
            f"Нельзя удалить рейс: есть {confirmed} подтверждённых бронирований."
        )

    conn.execute("DELETE FROM flights WHERE flight_id = ?", (flight_id,))
    conn.commit()
    conn.close()

def get_all_airports() -> list[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT airport_id, iata_code, city, country FROM airports ORDER BY city"
    ).fetchall()
    conn.close()
    return rows

def get_all_aircrafts() -> list[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT aircraft_id, reg_number, model, capacity
        FROM aircrafts
        WHERE status = 'active'
        ORDER BY model
    """).fetchall()
    conn.close()
    return rows
