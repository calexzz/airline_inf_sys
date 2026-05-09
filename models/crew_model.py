import sqlite3
from database.connection import get_connection

def get_all_crew() -> list[sqlite3.Row]:
    """Все члены экипажа с количеством выполненных рейсов"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            cm.crew_id,
            cm.last_name,
            cm.first_name,
            cm.role,
            cm.license_num,
            cm.license_exp,
            COUNT(fc.id)  AS flights_count,
            CAST(
                (julianday(cm.license_exp) - julianday('now')) / 30.44
            AS INTEGER)   AS months_left
        FROM crew_members cm
        LEFT JOIN flight_crew fc ON fc.crew_id = cm.crew_id
        GROUP BY cm.crew_id
        ORDER BY cm.role, cm.last_name
    """).fetchall()
    conn.close()
    return rows


def get_crew_by_id(crew_id: int) -> sqlite3.Row | None:
    """Один член экипажа по crew_id"""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM crew_members WHERE crew_id = ?", (crew_id,)
    ).fetchone()
    conn.close()
    return row


def search_crew(query: str) -> list[sqlite3.Row]:
    """Поиск по фамилии, имени или номеру лицензии"""
    like = f"%{query}%"
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            cm.crew_id,
            cm.last_name,
            cm.first_name,
            cm.role,
            cm.license_num,
            cm.license_exp
        FROM crew_members cm
        WHERE cm.last_name   LIKE ?
           OR cm.first_name  LIKE ?
           OR cm.license_num LIKE ?
        ORDER BY cm.last_name
    """, (like, like, like)).fetchall()
    conn.close()
    return rows

def get_expiring_licenses(months: int = 12) -> list[sqlite3.Row]:
    """
    Члены экипажа, у которых лицензия истекает в течение N месяцев.
    Используется для предупреждений в интерфейсе.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            cm.crew_id,
            cm.last_name,
            cm.first_name,
            cm.role,
            cm.license_num,
            cm.license_exp,
            CAST(
                (julianday(cm.license_exp) - julianday('now')) / 30.44
            AS INTEGER) AS months_left
        FROM crew_members cm
        WHERE julianday(cm.license_exp) - julianday('now') < ?
        ORDER BY cm.license_exp
    """, (months * 30.44,)).fetchall()
    conn.close()
    return rows

def get_crew_by_flight(flight_id: int) -> list[sqlite3.Row]:
    """Экипаж конкретного рейса"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            fc.id,
            cm.last_name || ' ' || cm.first_name  AS name,
            cm.role,
            fc.position,
            cm.license_num,
            cm.license_exp
        FROM flight_crew fc
        JOIN crew_members cm ON fc.crew_id = cm.crew_id
        WHERE fc.flight_id = ?
        ORDER BY cm.role
    """, (flight_id,)).fetchall()
    conn.close()
    return rows

def get_flights_by_crew(crew_id: int) -> list[sqlite3.Row]:
    """Рейсы, на которые назначен сотрудник"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            f.flight_number,
            a1.city     AS origin_city,
            a2.city     AS dest_city,
            f.departure_time,
            f.arrival_time,
            fc.position,
            f.status
        FROM flight_crew fc
        JOIN flights   f  ON fc.flight_id = f.flight_id
        JOIN airports a1  ON f.origin_id  = a1.airport_id
        JOIN airports a2  ON f.dest_id    = a2.airport_id
        WHERE fc.crew_id = ?
        ORDER BY f.departure_time
    """, (crew_id,)).fetchall()
    conn.close()
    return rows

def add_crew_member(
    last_name: str,
    first_name: str,
    role: str,
    license_num: str,
    license_exp: str,
) -> int:
    """Добавляет члена экипажа. Возвращает crew_id."""
    allowed_roles = {"captain", "first_officer", "flight_attendant"}
    if role not in allowed_roles:
        raise ValueError(f"Недопустимая роль: {role}. Допустимые: {allowed_roles}")

    conn = get_connection()
    exists = conn.execute(
        "SELECT crew_id FROM crew_members WHERE license_num = ?", (license_num,)
    ).fetchone()
    if exists:
        conn.close()
        raise ValueError(f"Лицензия {license_num} уже зарегистрирована.")

    cur = conn.execute("""
        INSERT INTO crew_members (last_name, first_name, role, license_num, license_exp)
        VALUES (?, ?, ?, ?, ?)
    """, (last_name, first_name, role, license_num, license_exp))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def assign_crew_to_flight(flight_id: int, crew_id: int, position: str) -> int:
    """
    Назначает члена экипажа на рейс.
    Проверяет: сотрудник ещё не назначен на этот рейс.
    Возвращает id записи flight_crew.
    """
    conn = get_connection()

    already = conn.execute("""
        SELECT id FROM flight_crew
        WHERE flight_id = ? AND crew_id = ?
    """, (flight_id, crew_id)).fetchone()
    if already:
        conn.close()
        raise ValueError("Сотрудник уже назначен на этот рейс.")

    cur = conn.execute("""
        INSERT INTO flight_crew (flight_id, crew_id, position)
        VALUES (?, ?, ?)
    """, (flight_id, crew_id, position))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id

def update_crew_member(
    crew_id: int,
    last_name: str,
    first_name: str,
    role: str,
    license_exp: str,
) -> None:
    """Обновляет данные сотрудника"""
    conn = get_connection()
    conn.execute("""
        UPDATE crew_members
        SET last_name   = ?,
            first_name  = ?,
            role        = ?,
            license_exp = ?
        WHERE crew_id = ?
    """, (last_name, first_name, role, license_exp, crew_id))
    conn.commit()
    conn.close()

def remove_crew_from_flight(flight_id: int, crew_id: int) -> None:
    """Снимает сотрудника с рейса."""
    conn = get_connection()
    conn.execute("""
        DELETE FROM flight_crew
        WHERE flight_id = ? AND crew_id = ?
    """, (flight_id, crew_id))
    conn.commit()
    conn.close()


def delete_crew_member(crew_id: int) -> None:
    """Удаляет сотрудника. Нельзя удалить если есть назначения на рейсы"""
    conn = get_connection()
    assigned = conn.execute(
        "SELECT COUNT(*) FROM flight_crew WHERE crew_id = ?", (crew_id,)
    ).fetchone()[0]

    if assigned > 0:
        conn.close()
        raise ValueError(
            f"Нельзя удалить сотрудника: назначен на {assigned} рейс(ов)."
        )

    conn.execute("DELETE FROM crew_members WHERE crew_id = ?", (crew_id,))
    conn.commit()
    conn.close()
