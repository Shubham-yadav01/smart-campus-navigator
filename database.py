import sqlite3
import os
from typing import Dict, Any, List, Optional
from werkzeug.security import generate_password_hash, check_password_hash

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'campus.db')
SCHEMA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')


def get_db_connection() -> sqlite3.Connection:
    """Creates and returns a connection to the SQLite database with Row factory."""
    conn = sqlite3.connect(DB_FILE, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Initializes the database schema if tables do not exist."""
    conn = get_db_connection()
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()


def get_all_buildings(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetches all buildings, optionally filtered by category, with department and facility summaries."""
    conn = get_db_connection()
    try:
        query = """
            SELECT 
                b.*,
                COUNT(DISTINCT d.id) AS department_count,
                COUNT(DISTINCT f.id) AS facility_count,
                GROUP_CONCAT(DISTINCT d.name) AS department_names
            FROM buildings b
            LEFT JOIN departments d ON b.id = d.building_id
            LEFT JOIN facilities f ON b.id = f.building_id
        """
        params = []
        if category and category.lower() != 'all':
            query += " WHERE LOWER(b.category) = LOWER(?)"
            params.append(category)

        query += " GROUP BY b.id ORDER BY b.name ASC"

        rows = conn.execute(query, params).fetchall()
        buildings = []
        for row in rows:
            b_dict = dict(row)
            # Parse comma-separated department names into a list
            if b_dict.get('department_names'):
                b_dict['departments'] = [d.strip() for d in b_dict['department_names'].split(',') if d.strip()]
            else:
                b_dict['departments'] = []
            buildings.append(b_dict)
        return buildings
    finally:
        conn.close()


def get_building_by_id(building_id: int) -> Optional[Dict[str, Any]]:
    """Fetches detailed information for a specific building, including departments and facilities."""
    conn = get_db_connection()
    try:
        building_row = conn.execute("SELECT * FROM buildings WHERE id = ?", (building_id,)).fetchone()
        if not building_row:
            return None

        building = dict(building_row)

        dept_rows = conn.execute(
            "SELECT * FROM departments WHERE building_id = ? ORDER BY name ASC",
            (building_id,)
        ).fetchall()
        building['departments'] = [dict(d) for d in dept_rows]

        facility_rows = conn.execute(
            "SELECT * FROM facilities WHERE building_id = ? ORDER BY floor ASC, name ASC",
            (building_id,)
        ).fetchall()
        building['facilities'] = [dict(f) for f in facility_rows]

        return building
    finally:
        conn.close()


def get_categories() -> List[Dict[str, Any]]:
    """Returns list of distinct building categories with counts."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT category, COUNT(*) as count 
            FROM buildings 
            GROUP BY category 
            ORDER BY category ASC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_campus_stats() -> Dict[str, Any]:
    """Returns summary statistics for the campus."""
    conn = get_db_connection()
    try:
        buildings_count = conn.execute("SELECT COUNT(*) FROM buildings").fetchone()[0]
        departments_count = conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0]
        facilities_count = conn.execute("SELECT COUNT(*) FROM facilities").fetchone()[0]
        total_rooms = conn.execute("SELECT SUM(total_rooms) FROM buildings").fetchone()[0] or 0
        categories_count = conn.execute("SELECT COUNT(DISTINCT category) FROM buildings").fetchone()[0]

        return {
            "total_buildings": buildings_count,
            "total_departments": departments_count,
            "total_facilities": facilities_count,
            "total_rooms": total_rooms,
            "total_categories": categories_count
        }
    finally:
        conn.close()


def search_campus(query: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Unified search across buildings, departments, and facilities/rooms.
    Returns matched results categorized by type.
    """
    clean_query = query.strip()
    if not clean_query:
        return {"buildings": [], "departments": [], "facilities": []}

    like_param = f"%{clean_query}%"
    conn = get_db_connection()
    try:
        # Search buildings
        building_rows = conn.execute("""
            SELECT id, name, code, category, description, floors, opening_hours, icon, badge_color
            FROM buildings
            WHERE name LIKE ? OR code LIKE ? OR description LIKE ? OR category LIKE ?
            ORDER BY name ASC
            LIMIT 10
        """, (like_param, like_param, like_param, like_param)).fetchall()

        # Search departments with building info
        dept_rows = conn.execute("""
            SELECT d.id, d.name, d.head_of_dept, d.contact_email, d.phone, d.room_number,
                   b.id as building_id, b.name as building_name, b.code as building_code
            FROM departments d
            JOIN buildings b ON d.building_id = b.id
            WHERE d.name LIKE ? OR d.contact_email LIKE ? OR d.room_number LIKE ?
            ORDER BY d.name ASC
            LIMIT 10
        """, (like_param, like_param, like_param)).fetchall()

        # Search facilities / rooms with building info
        facility_rows = conn.execute("""
            SELECT f.id, f.name, f.type, f.floor, f.room_number, f.status, f.description,
                   b.id as building_id, b.name as building_name, b.code as building_code
            FROM facilities f
            JOIN buildings b ON f.building_id = b.id
            WHERE f.name LIKE ? OR f.room_number LIKE ? OR f.type LIKE ? OR f.description LIKE ?
            ORDER BY f.name ASC
            LIMIT 15
        """, (like_param, like_param, like_param, like_param)).fetchall()

        return {
            "buildings": [dict(r) for r in building_rows],
            "departments": [dict(r) for r in dept_rows],
            "facilities": [dict(r) for r in facility_rows]
        }
    finally:
        conn.close()


def get_all_locations() -> List[Dict[str, Any]]:
    """Fetches all campus locations with coordinates for map markers and pathfinding."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT id, name, code, category, description, floors, total_rooms,
                   opening_hours, latitude, longitude, badge_color, icon
            FROM buildings
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY name ASC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_pathways() -> List[Dict[str, Any]]:
    """Fetches all pathway edges in the campus graph."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT p.*, 
                   b1.name as from_name, b1.code as from_code,
                   b2.name as to_name, b2.code as to_code
            FROM pathways p
            JOIN buildings b1 ON p.from_building_id = b1.id
            JOIN buildings b2 ON p.to_building_id = b2.id
            ORDER BY p.id ASC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_campus_graph_data() -> Dict[str, Any]:
    """
    Returns nodes dictionary and adjacency list for pathfinding.
    Graph is bidirectional: an edge from A to B allows travel B to A.
    """
    conn = get_db_connection()
    try:
        building_rows = conn.execute("SELECT * FROM buildings WHERE latitude IS NOT NULL").fetchall()
        nodes = {r['id']: dict(r) for r in building_rows}

        pathway_rows = conn.execute("SELECT * FROM pathways").fetchall()
        adjacency: Dict[int, List[Dict[str, Any]]] = {node_id: [] for node_id in nodes}

        for p in pathway_rows:
            u = p['from_building_id']
            v = p['to_building_id']
            dist = float(p['distance_meters'])
            name = p['pathway_name'] or 'Campus Walkway'

            if u in adjacency and v in adjacency:
                adjacency[u].append({"to": v, "distance": dist, "name": name})
                adjacency[v].append({"to": u, "distance": dist, "name": name})

        return {"nodes": nodes, "adjacency": adjacency}
    finally:
        conn.close()


# ---------------- Admin Authentication & Management ---------------- #

def get_admin_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Fetches an admin user record by username."""
    if not username:
        return None
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM admin_users WHERE LOWER(username) = LOWER(?)",
            (username.strip(),)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_admin_by_id(admin_id: int) -> Optional[Dict[str, Any]]:
    """Fetches an admin user record by primary key ID."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM admin_users WHERE id = ?",
            (admin_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_admin_user(username: str, password_raw: str, email: Optional[str] = None) -> int:
    """
    Creates a new admin user with a securely hashed password.
    Returns the new admin user's database ID.
    """
    username_clean = username.strip()
    if not username_clean:
        raise ValueError("Admin username cannot be empty.")
    if not password_raw or len(password_raw) < 6:
        raise ValueError("Admin password must be at least 6 characters.")

    password_hash = generate_password_hash(password_raw)
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "INSERT INTO admin_users (username, password_hash, email) VALUES (?, ?, ?)",
            (username_clean, password_hash, email.strip() if email else None)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def verify_admin_password(password_hash: str, password_raw: str) -> bool:
    """Verifies a plain text password against the stored PBKDF2/scrypt hash."""
    if not password_hash or not password_raw:
        return False
    return check_password_hash(password_hash, password_raw)


def update_admin_last_login(admin_id: int) -> None:
    """Updates the last_login timestamp for the given admin user."""
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE admin_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (admin_id,)
        )
        conn.commit()
    finally:
        conn.close()


def ensure_default_admin() -> Optional[int]:
    """
    Ensures at least one administrator account exists in the database.
    If no admin user exists, seeds an initial default admin.
    """
    conn = get_db_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM admin_users").fetchone()[0]
        if count == 0:
            default_user = os.environ.get('CAMPUS_ADMIN_USER', 'admin')
            default_pass = os.environ.get('CAMPUS_ADMIN_PASSWORD', 'Admin@Campus2026!')
            default_email = os.environ.get('CAMPUS_ADMIN_EMAIL', 'admin@campus.edu')
            password_hash = generate_password_hash(default_pass)
            cur = conn.execute(
                "INSERT INTO admin_users (username, password_hash, email) VALUES (?, ?, ?)",
                (default_user, password_hash, default_email)
            )
            conn.commit()
            print(f"Initialized default campus administrator account ('{default_user}').")
            return cur.lastrowid
        return None
    finally:
        conn.close()


# ---------------- Building CRUD Operations ---------------- #

def get_building_by_code(code: str, exclude_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Checks if a building code exists, optionally excluding a specific building ID (for edits)."""
    if not code:
        return None
    conn = get_db_connection()
    try:
        if exclude_id is not None:
            row = conn.execute(
                "SELECT * FROM buildings WHERE UPPER(code) = UPPER(?) AND id != ?",
                (code.strip(), exclude_id)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM buildings WHERE UPPER(code) = UPPER(?)",
                (code.strip(),)
            ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def add_building(data: Dict[str, Any]) -> int:
    """
    Inserts a new building record into the database.
    Returns the newly created building ID.
    """
    conn = get_db_connection()
    try:
        name = str(data.get('name', '')).strip()
        code = str(data.get('code', '')).strip().upper()
        category = str(data.get('category', 'Academic')).strip()
        description = str(data.get('description', '')).strip() if data.get('description') else None

        try:
            floors = int(data.get('floors') or 1)
        except (ValueError, TypeError):
            floors = 1

        try:
            total_rooms = int(data.get('total_rooms') or 1)
        except (ValueError, TypeError):
            total_rooms = 1

        opening_hours = str(data.get('opening_hours', '')).strip() if data.get('opening_hours') else '08:00 AM - 08:00 PM (Daily)'

        lat_val = data.get('latitude')
        if lat_val is not None and str(lat_val).strip() != '':
            try:
                latitude = float(lat_val)
            except (ValueError, TypeError):
                latitude = None
        else:
            latitude = None

        lng_val = data.get('longitude')
        if lng_val is not None and str(lng_val).strip() != '':
            try:
                longitude = float(lng_val)
            except (ValueError, TypeError):
                longitude = None
        else:
            longitude = None

        badge_color = str(data.get('badge_color', 'indigo') or 'indigo').strip()
        icon = str(data.get('icon', 'fa-building') or 'fa-building').strip()

        cur = conn.execute("""
            INSERT INTO buildings (
                name, code, category, description, floors, total_rooms,
                opening_hours, latitude, longitude, badge_color, icon
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, code, category, description, floors, total_rooms,
            opening_hours, latitude, longitude, badge_color, icon
        ))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_building(building_id: int, data: Dict[str, Any]) -> bool:
    """
    Updates an existing building record in the database.
    Returns True if the row was updated, False if building was not found.
    """
    conn = get_db_connection()
    try:
        name = str(data.get('name', '')).strip()
        code = str(data.get('code', '')).strip().upper()
        category = str(data.get('category', 'Academic')).strip()
        description = str(data.get('description', '')).strip() if data.get('description') else None

        try:
            floors = int(data.get('floors') or 1)
        except (ValueError, TypeError):
            floors = 1

        try:
            total_rooms = int(data.get('total_rooms') or 1)
        except (ValueError, TypeError):
            total_rooms = 1

        opening_hours = str(data.get('opening_hours', '')).strip() if data.get('opening_hours') else '08:00 AM - 08:00 PM (Daily)'

        lat_val = data.get('latitude')
        if lat_val is not None and str(lat_val).strip() != '':
            try:
                latitude = float(lat_val)
            except (ValueError, TypeError):
                latitude = None
        else:
            latitude = None

        lng_val = data.get('longitude')
        if lng_val is not None and str(lng_val).strip() != '':
            try:
                longitude = float(lng_val)
            except (ValueError, TypeError):
                longitude = None
        else:
            longitude = None

        badge_color = str(data.get('badge_color', 'indigo') or 'indigo').strip()
        icon = str(data.get('icon', 'fa-building') or 'fa-building').strip()

        cur = conn.execute("""
            UPDATE buildings SET
                name = ?,
                code = ?,
                category = ?,
                description = ?,
                floors = ?,
                total_rooms = ?,
                opening_hours = ?,
                latitude = ?,
                longitude = ?,
                badge_color = ?,
                icon = ?
            WHERE id = ?
        """, (
            name, code, category, description, floors, total_rooms,
            opening_hours, latitude, longitude, badge_color, icon,
            int(building_id)
        ))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_building(building_id: int) -> bool:
    """
    Deletes a building by its ID. Cascades deletion to departments, facilities,
    and pathways associated with the building.
    Returns True if building existed and was deleted, False otherwise.
    """
    conn = get_db_connection()
    try:
        b_id = int(building_id)
        conn.execute("DELETE FROM pathways WHERE from_building_id = ? OR to_building_id = ?", (b_id, b_id))
        conn.execute("DELETE FROM facilities WHERE building_id = ?", (b_id,))
        conn.execute("DELETE FROM departments WHERE building_id = ?", (b_id,))
        cur = conn.execute("DELETE FROM buildings WHERE id = ?", (b_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_admin_dashboard_stats() -> Dict[str, Any]:
    """
    Aggregates comprehensive dashboard metrics for the administration panel:
    campus stats, total admins, recent buildings, and category distribution.
    """
    conn = get_db_connection()
    try:
        base_stats = get_campus_stats()

        admin_count = conn.execute("SELECT COUNT(*) FROM admin_users").fetchone()[0]

        recent_rows = conn.execute("""
            SELECT id, name, code, category, floors, total_rooms, created_at, badge_color, icon
            FROM buildings
            ORDER BY id DESC
            LIMIT 5
        """).fetchall()

        recent_buildings = [dict(r) for r in recent_rows]

        categories_rows = conn.execute("""
            SELECT category, COUNT(*) as count
            FROM buildings
            GROUP BY category
            ORDER BY count DESC, category ASC
        """).fetchall()
        categories_breakdown = [dict(r) for r in categories_rows]

        return {
            **base_stats,
            "total_admins": admin_count,
            "recent_buildings": recent_buildings,
            "categories_breakdown": categories_breakdown
        }
    finally:
        conn.close()