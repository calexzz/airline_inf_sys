import sqlite3
from datetime import datetime
from database.connection import get_connection

def get_all_bookings() -> list[sqlite3.Row]:
    """Все бронирования с данными пассажира и рейса."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            b.booking_id,
            p.last_name || ' ' || p.first_name  AS passenger_name,
            p.passport_num,
            f.flight_number,
            a1.city     AS origin_city,
            a2.city     AS dest_city,
            f.departure_time,
            b.seat_number,
            b.class,
            b.price,
            b.status,
            b.booked_at
        FROM bookings b
        JOIN passengers p ON b.passenger_id = p.passenger_id
        JOIN flights    f ON b.flight_id    = f.flight_id
        JOIN airports  a1 ON f.origin_id    = a1.airport_id
        JOIN airports  a2 ON f.dest_id      = a2.airport_id
        ORDER BY b.booked_at DESC
    """).fetchall()
    conn.close()
    return rows

def get_bookings_by_flight(flight_id: int) -> list[sqlite3.Row]:
    """Список пассажиров на конкретный рейс"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            b.booking_id,
            p.last_name,
            p.first_name,
            p.passport_num,
            b.seat_number,
            b.class,
            b.price,
            b.status
        FROM bookings b
        JOIN passengers p ON b.passenger_id = p.passenger_id
        WHERE b.flight_id = ?
        ORDER BY b.seat_number
    """, (flight_id,)).fetchall()
    conn.close()
    return rows


def get_bookings_by_passenger(passenger_id: int) -> list[sqlite3.Row]:
    """Все брони конкретного пассажира"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            b.booking_id,
            f.flight_number,
            a1.city     AS origin_city,
            a2.city     AS dest_city,
            f.departure_time,
            b.seat_number,
            b.class,
            b.price,
            b.status
        FROM bookings b
        JOIN flights   f ON b.flight_id  = f.flight_id
        JOIN airports a1 ON f.origin_id  = a1.airport_id
        JOIN airports a2 ON f.dest_id    = a2.airport_id
        WHERE b.passenger_id = ?
        ORDER BY f.departure_time DESC
    """, (passenger_id,)).fetchall()
    conn.close()
    return rows

def get_booking_by_id(booking_id: int) -> sqlite3.Row | None:
    """Одна бронь по booking_id"""
    conn = get_connection()
    row = conn.execute("""
        SELECT
            b.booking_id,
            p.last_name || ' ' || p.first_name AS passenger_name,
            p.passport_num,
            f.flight_number,
            a1.city     AS origin_city,
            a2.city     AS dest_city,
            f.departure_time,
            b.seat_number,
            b.class,
            b.price,
            b.status,
            b.booked_at
        FROM bookings b
        JOIN passengers p ON b.passenger_id = p.passenger_id
        JOIN flights    f ON b.flight_id    = f.flight_id
        JOIN airports  a1 ON f.origin_id    = a1.airport_id
        JOIN airports  a2 ON f.dest_id      = a2.airport_id
        WHERE b.booking_id = ?
    """, (booking_id,)).fetchone()
    conn.close()
    return row


def is_seat_taken(flight_id: int, seat_number: str) -> bool:
    """Проверяет, занято ли место на рейсе"""
    conn = get_connection()
    row = conn.execute("""
        SELECT booking_id FROM bookings
        WHERE flight_id = ? AND seat_number = ? AND status = 'confirmed'
    """, (flight_id, seat_number)).fetchone()
    conn.close()
    return row is not None

def add_booking(
    passenger_id: int,
    flight_id: int,
    seat_number: str,
    seat_class: str,
    price: float,
) -> int:
    """
    Создаёт бронирование. Проверяет:
    - место не занято
    - пассажир не летит уже на этом рейсе
    Возвращает booking_id.
    """
    conn = get_connection()

    seat_taken = conn.execute("""
        SELECT booking_id FROM bookings
        WHERE flight_id = ? AND seat_number = ? AND status = 'confirmed'
    """, (flight_id, seat_number)).fetchone()
    if seat_taken:
        conn.close()
        raise ValueError(f"Место {seat_number} уже занято.")

    already = conn.execute("""
        SELECT booking_id FROM bookings
        WHERE passenger_id = ? AND flight_id = ? AND status = 'confirmed'
    """, (passenger_id, flight_id)).fetchone()
    if already:
        conn.close()
        raise ValueError("Пассажир уже забронирован на этот рейс.")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute("""
        INSERT INTO bookings
            (passenger_id, flight_id, seat_number, class, price, status, booked_at)
        VALUES (?, ?, ?, ?, ?, 'confirmed', ?)
    """, (passenger_id, flight_id, seat_number, seat_class, price, now))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id

def cancel_booking(booking_id: int) -> None:
    """Отменяет бронирование"""
    conn = get_connection()

    booking = conn.execute(
        "SELECT status FROM bookings WHERE booking_id = ?", (booking_id,)
    ).fetchone()

    if not booking:
        conn.close()
        raise ValueError(f"Бронирование {booking_id} не найдено.")
    if booking["status"] == "cancelled":
        conn.close()
        raise ValueError("Бронирование уже отменено.")

    conn.execute(
        "UPDATE bookings SET status = 'cancelled' WHERE booking_id = ?",
        (booking_id,)
    )
    conn.commit()
    conn.close()


def update_booking_status(booking_id: int, status: str) -> None:
    """Смена статуса: confirmed / cancelled / used"""
    allowed = {"confirmed", "cancelled", "used"}
    if status not in allowed:
        raise ValueError(f"Недопустимый статус: {status}. Допустимые: {allowed}")

    conn = get_connection()
    conn.execute(
        "UPDATE bookings SET status = ? WHERE booking_id = ?",
        (status, booking_id)
    )
    conn.commit()
    conn.close()

def delete_booking(booking_id: int) -> None:
    """Полное удаление записи о бронировании"""
    conn = get_connection()
    conn.execute("DELETE FROM bookings WHERE booking_id = ?", (booking_id,))
    conn.commit()
    conn.close()

def get_revenue_by_flight() -> list[sqlite3.Row]:
    """Выручка по каждому рейсу"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            f.flight_number,
            a1.city || ' → ' || a2.city     AS route,
            COUNT(b.booking_id)              AS bookings_count,
            COALESCE(SUM(b.price), 0)        AS revenue,
            ROUND(AVG(b.price), 2)           AS avg_price
        FROM flights f
        JOIN airports a1 ON f.origin_id = a1.airport_id
        JOIN airports a2 ON f.dest_id   = a2.airport_id
        LEFT JOIN bookings b
               ON b.flight_id = f.flight_id AND b.status = 'confirmed'
        GROUP BY f.flight_id
        ORDER BY revenue DESC
    """).fetchall()
    conn.close()
    return rows
