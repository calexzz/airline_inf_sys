import sqlite3
from database.connection import get_connection

def get_all_passengers() -> list[sqlite3.Row]:
    """Все пассажиры, отсортированные по фамилии"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            p.passenger_id,
            p.last_name,
            p.first_name,
            p.passport_num,
            p.email,
            p.phone,
            COUNT(b.booking_id) AS total_flights
        FROM passengers p
        LEFT JOIN bookings b
               ON b.passenger_id = p.passenger_id
              AND b.status = 'confirmed'
        GROUP BY p.passenger_id
        ORDER BY p.last_name, p.first_name
    """).fetchall()
    conn.close()
    return rows

def get_passenger_by_id(passenger_id: int) -> sqlite3.Row | None:
    """Один пассажир по passenger_id"""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM passengers WHERE passenger_id = ?",
        (passenger_id,)
    ).fetchone()
    conn.close()
    return row


def get_passenger_by_passport(passport_num: str) -> sqlite3.Row | None:
    """Поиск по номеру паспорта"""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM passengers WHERE passport_num = ?",
        (passport_num,)
    ).fetchone()
    conn.close()
    return row


def search_passengers(query: str) -> list[sqlite3.Row]:
    """Поиск по фамилии, имени, паспорту или email"""
    like = f"%{query}%"
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            p.passenger_id,
            p.last_name,
            p.first_name,
            p.passport_num,
            p.email,
            p.phone
        FROM passengers p
        WHERE p.last_name    LIKE ?
           OR p.first_name   LIKE ?
           OR p.passport_num LIKE ?
           OR p.email        LIKE ?
        ORDER BY p.last_name
    """, (like, like, like, like)).fetchall()
    conn.close()
    return rows


def get_passenger_history(passenger_id: int) -> list[sqlite3.Row]:
    """История рейсов пассажира."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            f.flight_number,
            a1.city     AS origin_city,
            a2.city     AS dest_city,
            f.departure_time,
            b.seat_number,
            b.class,
            b.price,
            b.status    AS booking_status
        FROM bookings b
        JOIN flights  f  ON b.flight_id  = f.flight_id
        JOIN airports a1 ON f.origin_id  = a1.airport_id
        JOIN airports a2 ON f.dest_id    = a2.airport_id
        WHERE b.passenger_id = ?
        ORDER BY f.departure_time DESC
    """, (passenger_id,)).fetchall()
    conn.close()
    return rows

def add_passenger(
    last_name: str,
    first_name: str,
    passport_num: str,
    email: str,
    phone: str,
) -> int:
    """Добавляет пассажира. Возвращает passenger_id"""
    conn = get_connection()

    # Проверка уникальности паспорта
    exists = conn.execute(
        "SELECT passenger_id FROM passengers WHERE passport_num = ?",
        (passport_num,)
    ).fetchone()
    if exists:
        conn.close()
        raise ValueError(f"Пассажир с паспортом {passport_num} уже существует.")

    cur = conn.execute("""
        INSERT INTO passengers (last_name, first_name, passport_num, email, phone)
        VALUES (?, ?, ?, ?, ?)
    """, (last_name, first_name, passport_num, email, phone))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id

def update_passenger(
    passenger_id: int,
    last_name: str,
    first_name: str,
    email: str,
    phone: str,
) -> None:
    """Обновляет контактные данные пассажира (паспорт не меняется)"""
    conn = get_connection()
    conn.execute("""
        UPDATE passengers
        SET last_name  = ?,
            first_name = ?,
            email      = ?,
            phone      = ?
        WHERE passenger_id = ?
    """, (last_name, first_name, email, phone, passenger_id))
    conn.commit()
    conn.close()

def delete_passenger(passenger_id: int) -> None:
    """Удаляет пассажира. Нельзя удалить если есть подтверждённые брони"""
    conn = get_connection()
    confirmed = conn.execute("""
        SELECT COUNT(*) FROM bookings
        WHERE passenger_id = ? AND status = 'confirmed'
    """, (passenger_id,)).fetchone()[0]

    if confirmed > 0:
        conn.close()
        raise ValueError(
            f"Нельзя удалить пассажира: есть {confirmed} подтверждённых бронирований."
        )

    conn.execute("DELETE FROM passengers WHERE passenger_id = ?", (passenger_id,))
    conn.commit()
    conn.close()
