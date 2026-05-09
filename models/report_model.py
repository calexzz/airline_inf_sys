import sqlite3
from database.connection import get_connection

def get_revenue_by_flight() -> list[sqlite3.Row]:
    """
    Выручка, средний чек, мин/макс цена по каждому рейсу.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            f.flight_number,
            a1.city || ' - ' || a2.city          AS route,
            COUNT(b.booking_id)                   AS bookings_count,
            COALESCE(SUM(b.price),  0)            AS revenue,
            COALESCE(ROUND(AVG(b.price), 2), 0)   AS avg_price,
            COALESCE(MAX(b.price), 0)             AS max_price,
            COALESCE(MIN(b.price), 0)             AS min_price
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

def get_revenue_by_route() -> list[sqlite3.Row]:
    """
    Суммарная выручка по маршрутам (без разбивки по рейсам).
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            a1.city || ' - ' || a2.city   AS route,
            COUNT(b.booking_id)            AS bookings_count,
            COALESCE(SUM(b.price), 0)      AS revenue
        FROM flights f
        JOIN airports a1 ON f.origin_id = a1.airport_id
        JOIN airports a2 ON f.dest_id   = a2.airport_id
        LEFT JOIN bookings b
               ON b.flight_id = f.flight_id AND b.status = 'confirmed'
        GROUP BY a1.airport_id, a2.airport_id
        ORDER BY revenue DESC
    """).fetchall()
    conn.close()
    return rows

def get_revenue_summary() -> sqlite3.Row:
    """
    Общая статистика одной строкой:
    total_revenue, total_bookings, avg_price, cancelled_count.
    """
    conn = get_connection()
    row = conn.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN status = 'confirmed' THEN price END), 0)
                                                        AS total_revenue,
            COUNT(CASE WHEN status = 'confirmed' THEN 1 END)
                                                        AS total_bookings,
            COALESCE(ROUND(AVG(CASE WHEN status = 'confirmed' THEN price END), 2), 0)
                                                        AS avg_price,
            COUNT(CASE WHEN status = 'cancelled' THEN 1 END)
                                                        AS cancelled_count,
            COUNT(DISTINCT passenger_id)                AS unique_passengers
        FROM bookings
    """).fetchone()
    conn.close()
    return row

def get_flight_load_all() -> list[sqlite3.Row]:
    """
    Процент заполненности каждого рейса
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            f.flight_number,
            a1.city || ' - ' || a2.city             AS route,
            f.departure_time,
            ac.capacity,
            COUNT(b.booking_id)                      AS sold,
            ac.capacity - COUNT(b.booking_id)        AS free,
            ROUND(
                100.0 * COUNT(b.booking_id) / ac.capacity, 1
            )                                        AS load_pct,
            f.status
        FROM flights f
        JOIN airports  a1 ON f.origin_id   = a1.airport_id
        JOIN airports  a2 ON f.dest_id     = a2.airport_id
        JOIN aircrafts ac ON f.aircraft_id = ac.aircraft_id
        LEFT JOIN bookings b
               ON b.flight_id = f.flight_id AND b.status = 'confirmed'
        GROUP BY f.flight_id
        ORDER BY load_pct DESC
    """).fetchall()
    conn.close()
    return rows


def get_load_by_class() -> list[sqlite3.Row]:
    """
    Разбивка бронирований по классу обслуживания (economy / business).
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            class,
            COUNT(*)             AS count,
            COALESCE(SUM(price), 0) AS revenue,
            ROUND(
                100.0 * COUNT(*) / (SELECT COUNT(*) FROM bookings WHERE status = 'confirmed'),
                1
            )                    AS share_pct
        FROM bookings
        WHERE status = 'confirmed'
        GROUP BY class
        ORDER BY count DESC
    """).fetchall()
    conn.close()
    return rows

def get_passenger_ranking() -> list[sqlite3.Row]:
    """
    Рейтинг пассажиров по суммарным расходам. Программа лояльности
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            p.passenger_id,
            p.last_name || ' ' || p.first_name  AS passenger_name,
            p.email,
            COUNT(b.booking_id)                  AS flights_count,
            SUM(b.price)                         AS total_spent,
            RANK() OVER (ORDER BY SUM(b.price) DESC) AS rank
        FROM passengers p
        JOIN bookings b ON b.passenger_id = p.passenger_id
        WHERE b.status = 'confirmed'
        GROUP BY p.passenger_id
        ORDER BY total_spent DESC
    """).fetchall()
    conn.close()
    return rows


def get_top_passengers(limit: int = 5) -> list[sqlite3.Row]:
    """Топ-N пассажиров по расходам. Для виджета на главном экране"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            p.last_name || ' ' || p.first_name  AS passenger_name,
            COUNT(b.booking_id)                  AS flights_count,
            SUM(b.price)                         AS total_spent
        FROM passengers p
        JOIN bookings b ON b.passenger_id = p.passenger_id
        WHERE b.status = 'confirmed'
        GROUP BY p.passenger_id
        ORDER BY total_spent DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows

def get_crew_workload() -> list[sqlite3.Row]:
    """
    Нагрузка на каждого члена экипажа - сколько рейсов назначено.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            cm.last_name || ' ' || cm.first_name  AS crew_name,
            cm.role,
            COUNT(fc.id)                           AS flights_assigned,
            cm.license_exp,
            CAST(
                (julianday(cm.license_exp) - julianday('now')) / 30.44
            AS INTEGER)                            AS months_left
        FROM crew_members cm
        LEFT JOIN flight_crew fc ON fc.crew_id = cm.crew_id
        GROUP BY cm.crew_id
        ORDER BY flights_assigned DESC
    """).fetchall()
    conn.close()
    return rows


def get_expiring_licenses(months: int = 12) -> list[sqlite3.Row]:
    """
    Сотрудники с истекающими лицензиями - для предупреждений
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            cm.last_name || ' ' || cm.first_name  AS crew_name,
            cm.role,
            cm.license_num,
            cm.license_exp,
            CAST(
                (julianday(cm.license_exp) - julianday('now')) / 30.44
            AS INTEGER)                            AS months_left
        FROM crew_members cm
        WHERE julianday(cm.license_exp) - julianday('now') < ?
        ORDER BY cm.license_exp
    """, (months * 30.44,)).fetchall()
    conn.close()
    return rows

def get_aircraft_util() -> list[sqlite3.Row]:
    """
    ВС: сколько рейсов выполнено,
    суммарная выручка на борту.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            ac.reg_number,
            ac.model,
            ac.capacity,
            ac.status,
            COUNT(DISTINCT f.flight_id)         AS flights_count,
            COALESCE(SUM(b.price), 0)           AS total_revenue
        FROM aircrafts ac
        LEFT JOIN flights  f ON f.aircraft_id  = ac.aircraft_id
        LEFT JOIN bookings b ON b.flight_id    = f.flight_id
                             AND b.status      = 'confirmed'
        GROUP BY ac.aircraft_id
        ORDER BY flights_count DESC
    """).fetchall()
    conn.close()
    return rows
