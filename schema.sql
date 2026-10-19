-- SQLite Schema for Smart Campus Navigator

CREATE TABLE IF NOT EXISTS buildings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    description TEXT,
    floors INTEGER DEFAULT 1,
    total_rooms INTEGER DEFAULT 1,
    opening_hours TEXT,
    latitude REAL,
    longitude REAL,
    badge_color TEXT DEFAULT 'indigo',
    icon TEXT DEFAULT 'fa-building',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    building_id INTEGER NOT NULL,
    head_of_dept TEXT,
    contact_email TEXT,
    phone TEXT,
    room_number TEXT,
    FOREIGN KEY (building_id) REFERENCES buildings (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS facilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    building_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    floor INTEGER DEFAULT 1,
    room_number TEXT,
    status TEXT DEFAULT 'Open',
    description TEXT,
    FOREIGN KEY (building_id) REFERENCES buildings (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_buildings_code ON buildings(code);
CREATE INDEX IF NOT EXISTS idx_buildings_category ON buildings(category);
CREATE INDEX IF NOT EXISTS idx_departments_building ON departments(building_id);
CREATE INDEX IF NOT EXISTS idx_facilities_building ON facilities(building_id);

CREATE TABLE IF NOT EXISTS pathways (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_building_id INTEGER NOT NULL,
    to_building_id INTEGER NOT NULL,
    distance_meters REAL NOT NULL,
    pathway_name TEXT,
    is_accessible INTEGER DEFAULT 1,
    FOREIGN KEY (from_building_id) REFERENCES buildings (id) ON DELETE CASCADE,
    FOREIGN KEY (to_building_id) REFERENCES buildings (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pathways_from ON pathways(from_building_id);
CREATE INDEX IF NOT EXISTS idx_pathways_to ON pathways(to_building_id);

CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admin_username ON admin_users(username);
