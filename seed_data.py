import sqlite3
import os
from database import DB_FILE, init_db, get_db_connection

BUILDINGS_DATA = [
    {
        "name": "Turing Hall of Computer Science & Engineering",
        "code": "ENG",
        "category": "Academic",
        "description": "Hub for computing disciplines, advanced robotics workshops, high-performance computing clusters, and collaborative team project spaces.",
        "floors": 4,
        "total_rooms": 54,
        "opening_hours": "07:00 AM - 11:00 PM (Daily)",
        "latitude": 37.4275,
        "longitude": -122.1697,
        "badge_color": "indigo",
        "icon": "fa-laptop-code",
        "departments": [
            {"name": "Computer Science & Engineering", "head_of_dept": "Dr. Alan Vance", "contact_email": "cs-dept@campus.edu", "phone": "+1 (555) 234-5001", "room_number": "ENG-301"},
            {"name": "Cybersecurity & Information Assurance", "head_of_dept": "Prof. Elena Rostova", "contact_email": "cyber@campus.edu", "phone": "+1 (555) 234-5002", "room_number": "ENG-210"},
            {"name": "Electrical & Computer Systems", "head_of_dept": "Dr. Marcus Wei", "contact_email": "ece@campus.edu", "phone": "+1 (555) 234-5003", "room_number": "ENG-115"}
        ],
        "facilities": [
            {"name": "Robotics & Autonomous Systems Lab", "type": "Lab", "floor": 3, "room_number": "302", "status": "Open", "description": "Features ROS robots, drone cages, and computer vision test beds."},
            {"name": "AI & Big Data Computing Center", "type": "Lab", "floor": 2, "room_number": "214", "status": "Open", "description": "GPU cluster workstations for machine learning and neural network training."},
            {"name": "Undergraduate Computing Lab A", "type": "Study Room", "floor": 1, "room_number": "101", "status": "Available", "description": "60 dual-monitor workstations open for student assignment work."}
        ]
    },
    {
        "name": "Academic Block - Science & Research Complex",
        "code": "SCI",
        "category": "Academic",
        "description": "Multi-disciplinary facility housing modern wet laboratories, chemical instrumentation rooms, physics experimental halls, and lecture auditoriums.",
        "floors": 5,
        "total_rooms": 68,
        "opening_hours": "08:00 AM - 09:30 PM (Mon-Sat)",
        "latitude": 37.4282,
        "longitude": -122.1685,
        "badge_color": "emerald",
        "icon": "fa-flask-vial",
        "departments": [
            {"name": "Chemistry & Chemical Biology", "head_of_dept": "Dr. Sarah Jenkins", "contact_email": "chemistry@campus.edu", "phone": "+1 (555) 234-5101", "room_number": "SCI-201"},
            {"name": "Physics & Astronomy", "head_of_dept": "Dr. David Thorne", "contact_email": "physics@campus.edu", "phone": "+1 (555) 234-5102", "room_number": "SCI-310"}
        ],
        "facilities": [
            {"name": "Organic Chemistry Research Lab", "type": "Lab", "floor": 2, "room_number": "205", "status": "Scheduled Access", "description": "Fume hoods, spectrometers, and chromatography stations."},
            {"name": "Laser Optics & Photonics Lab", "type": "Lab", "floor": 1, "room_number": "110", "status": "Open", "description": "Vibration-isolated optical tables for quantum and laser experiments."},
            {"name": "Science Auditorium Alpha", "type": "Auditorium", "floor": 1, "room_number": "100", "status": "Available", "description": "250-seat lecture theater equipped with tiered multimedia display."}
        ]
    },
    {
        "name": "Central Memorial Library & Learning Commons",
        "code": "LIB",
        "category": "Library",
        "description": "Main campus repository with over 600,000 volumes, digital archives, group project study pods, and 24-hour reading sanctuaries.",
        "floors": 4,
        "total_rooms": 32,
        "opening_hours": "Open 24/7 (Campus ID Required after 10 PM)",
        "latitude": 37.4268,
        "longitude": -122.1705,
        "badge_color": "amber",
        "icon": "fa-book-open",
        "departments": [
            {"name": "University Library Services", "head_of_dept": "Clara Higgins, MLS", "contact_email": "library@campus.edu", "phone": "+1 (555) 234-5201", "room_number": "LIB-102"},
            {"name": "Digital Archives & Special Collections", "head_of_dept": "Dr. Arthur Campbell", "contact_email": "archives@campus.edu", "phone": "+1 (555) 234-5202", "room_number": "LIB-401"}
        ],
        "facilities": [
            {"name": "24/7 Silent Study Sanctuary", "type": "Study Room", "floor": 3, "room_number": "301", "status": "Available", "description": "Absolute silence study hall with individual carrels and power docks."},
            {"name": "Media Creation & Podcasting Studio", "type": "Media Studio", "floor": 1, "room_number": "105", "status": "Open", "description": "Acoustic-treated sound booths with Shure microphones and video editing rigs."},
            {"name": "Campus IT Helpdesk & Device Rental", "type": "Service", "floor": 1, "room_number": "110", "status": "Open", "description": "Walk-in assistance for campus WiFi, accounts, and laptop loaners."}
        ]
    },
    {
        "name": "Chancellor Hall & Administrative Center",
        "code": "ADM",
        "category": "Administrative",
        "description": "Central administrative headquarters accommodating executive leadership, registrar services, bursar offices, and admissions reception.",
        "floors": 3,
        "total_rooms": 40,
        "opening_hours": "08:30 AM - 05:00 PM (Mon-Fri)",
        "latitude": 37.4260,
        "longitude": -122.1720,
        "badge_color": "slate",
        "icon": "fa-landmark",
        "departments": [
            {"name": "Office of the Chancellor", "head_of_dept": "Chancellor Raymond Alvarez", "contact_email": "chancellor@campus.edu", "phone": "+1 (555) 234-5301", "room_number": "ADM-300"},
            {"name": "Admissions & University Enrollment", "head_of_dept": "Miriam Gomez", "contact_email": "admissions@campus.edu", "phone": "+1 (555) 234-5302", "room_number": "ADM-101"},
            {"name": "Office of Financial Aid & Scholarships", "head_of_dept": "Thomas Sterling", "contact_email": "finaid@campus.edu", "phone": "+1 (555) 234-5303", "room_number": "ADM-120"}
        ],
        "facilities": [
            {"name": "Admissions Welcome Center", "type": "Service", "floor": 1, "room_number": "101", "status": "Open", "description": "Greeting desk and guided campus tour departure point."},
            {"name": "Student Financial Service Windows", "type": "Service", "floor": 1, "room_number": "120", "status": "Open", "description": "Counters for tuition payments, loan counseling, and grants."},
            {"name": "University Council Boardroom", "type": "Auditorium", "floor": 3, "room_number": "305", "status": "Scheduled Access", "description": "Executive meeting chambers for faculty senate and trustees."}
        ]
    },
    {
        "name": "University Student Union & Activity Center",
        "code": "STU",
        "category": "Student Life",
        "description": "Vibrant center of student social life featuring clubs headquarters, student government, gaming lounge, and campus bookshop.",
        "floors": 3,
        "total_rooms": 35,
        "opening_hours": "07:30 AM - Midnight (Daily)",
        "latitude": 37.4265,
        "longitude": -122.1690,
        "badge_color": "purple",
        "icon": "fa-users",
        "departments": [
            {"name": "Student Affairs & Campus Life", "head_of_dept": "Dean Karen Brooks", "contact_email": "studentaffairs@campus.edu", "phone": "+1 (555) 234-5401", "room_number": "STU-201"},
            {"name": "Associated Student Government (ASG)", "head_of_dept": "President Maya Patel", "contact_email": "asg@campus.edu", "phone": "+1 (555) 234-5402", "room_number": "STU-215"},
            {"name": "Career Development & Internship Hub", "head_of_dept": "Gregory Hayes", "contact_email": "careers@campus.edu", "phone": "+1 (555) 234-5403", "room_number": "STU-110"}
        ],
        "facilities": [
            {"name": "Campus Official Bookstore & Tech Store", "type": "Store", "floor": 1, "room_number": "101", "status": "Open", "description": "Textbooks, university merchandise, supplies, and electronics."},
            {"name": "Student Esports & Gaming Arena", "type": "Recreation", "floor": 2, "room_number": "205", "status": "Available", "description": "High-refresh gaming rigs and console lounge for students."},
            {"name": "Grand Multi-Purpose Event Hall", "type": "Auditorium", "floor": 1, "room_number": "150", "status": "Available", "description": "Hosts cultural evenings, career fairs, and hackathons."}
        ]
    },
    {
        "name": "Fleming Health & Life Sciences Pavilion",
        "code": "HLS",
        "category": "Academic",
        "description": "Modern health education complex equipped with hospital simulation suites, clinical psychology labs, and anatomy study facilities.",
        "floors": 4,
        "total_rooms": 48,
        "opening_hours": "07:30 AM - 09:00 PM (Mon-Sat)",
        "latitude": 37.4290,
        "longitude": -122.1712,
        "badge_color": "rose",
        "icon": "fa-heart-pulse",
        "departments": [
            {"name": "Department of Nursing & Patient Care", "head_of_dept": "Dr. Beatrice Ramos", "contact_email": "nursing@campus.edu", "phone": "+1 (555) 234-5501", "room_number": "HLS-200"},
            {"name": "Public Health & Epidemiology", "head_of_dept": "Dr. Julian Montgomery", "contact_email": "publichealth@campus.edu", "phone": "+1 (555) 234-5502", "room_number": "HLS-301"}
        ],
        "facilities": [
            {"name": "Clinical Simulation Hospital Ward", "type": "Lab", "floor": 2, "room_number": "210", "status": "Open", "description": "High-fidelity patient manikins and telemetry units for nursing training."},
            {"name": "Student Health & Wellness Clinic", "type": "Clinic", "floor": 1, "room_number": "104", "status": "Open", "description": "Primary healthcare, vaccinations, and first-aid services for campus community."},
            {"name": "Human Anatomy & Physiology Lab", "type": "Lab", "floor": 3, "room_number": "315", "status": "Scheduled Access", "description": "Anatomical models, 3D digital dissection tables, and microscopy sets."}
        ]
    },
    {
        "name": "Newton Mathematics & Physics Tower",
        "code": "MAT",
        "category": "Academic",
        "description": "Six-story academic tower with specialized mathematical modeling suites, blackboard lecture theaters, and statistical consulting services.",
        "floors": 6,
        "total_rooms": 62,
        "opening_hours": "08:00 AM - 10:00 PM (Daily)",
        "latitude": 37.4270,
        "longitude": -122.1678,
        "badge_color": "cyan",
        "icon": "fa-calculator",
        "departments": [
            {"name": "Department of Pure & Applied Mathematics", "head_of_dept": "Dr. Leonid Markov", "contact_email": "math@campus.edu", "phone": "+1 (555) 234-5601", "room_number": "MAT-401"},
            {"name": "Statistics & Actuarial Science", "head_of_dept": "Dr. Priya Nair", "contact_email": "stats@campus.edu", "phone": "+1 (555) 234-5602", "room_number": "MAT-501"}
        ],
        "facilities": [
            {"name": "Mathematics Peer Tutoring Lab", "type": "Study Room", "floor": 2, "room_number": "201", "status": "Available", "description": "Free walk-in tutoring for calculus, linear algebra, and differential equations."},
            {"name": "Quantum Computing & Modeling Suite", "type": "Lab", "floor": 5, "room_number": "504", "status": "Open", "description": "High-throughput numerical modeling and computational mathematics station."},
            {"name": "Newton Lecture Hall 101", "type": "Auditorium", "floor": 1, "room_number": "101", "status": "Open", "description": "Traditional triple-sliding slate blackboards with 180 seats."}
        ]
    },
    {
        "name": "Falcon Athletics & Recreation Complex",
        "code": "ARC",
        "category": "Sports",
        "description": "World-class sports center housing an Olympic-grade aquatics pavilion, weight training arena, multi-court gymnasium, and indoor jogging track.",
        "floors": 2,
        "total_rooms": 24,
        "opening_hours": "06:00 AM - 11:00 PM (Daily)",
        "latitude": 37.4295,
        "longitude": -122.1730,
        "badge_color": "orange",
        "icon": "fa-dumbbell",
        "departments": [
            {"name": "Intercollegiate Athletics Department", "head_of_dept": "Coach Darryl Washington", "contact_email": "athletics@campus.edu", "phone": "+1 (555) 234-5701", "room_number": "ARC-105"},
            {"name": "Campus Recreation & Intramurals", "head_of_dept": "Samantha Reed", "contact_email": "recreation@campus.edu", "phone": "+1 (555) 234-5702", "room_number": "ARC-108"}
        ],
        "facilities": [
            {"name": "Olympic 50m Aquatics Center", "type": "Sports Facility", "floor": 1, "room_number": "Pool-A", "status": "Open", "description": "Heated 50-meter lap pool, diving boards, and spectator seating."},
            {"name": "Cardio & Strength Training Arena", "type": "Gym", "floor": 2, "room_number": "201", "status": "Available", "description": "Free weights, power racks, kettlebells, and cardio machines."},
            {"name": "Multi-Court Arena (Basketball / Volleyball)", "type": "Sports Court", "floor": 1, "room_number": "Gym-1", "status": "Open", "description": "Three hardwood courts for basketball, volleyball, and badminton."}
        ]
    },
    {
        "name": "Campus Canteen & Dining Commons",
        "code": "DINE",
        "category": "Dining",
        "description": "Central dining hub featuring international cuisine stations, artisan bakery, coffee bar, and grab-and-go meal plans.",
        "floors": 2,
        "total_rooms": 16,
        "opening_hours": "07:00 AM - 10:00 PM (Daily)",
        "latitude": 37.4262,
        "longitude": -122.1680,
        "badge_color": "amber",
        "icon": "fa-utensils",
        "departments": [
            {"name": "Dining Services & Hospitality", "head_of_dept": "Chef Antoine Mercier", "contact_email": "dining@campus.edu", "phone": "+1 (555) 234-5801", "room_number": "DINE-102"}
        ],
        "facilities": [
            {"name": "Global Flavors Dining Hall", "type": "Cafeteria", "floor": 1, "room_number": "100", "status": "Open", "description": "Buffet stations including Asian wok, Italian hearth, Mediterranean grill, and vegan bar."},
            {"name": "The Roastery Campus Coffee & Bakery", "type": "Cafe", "floor": 1, "room_number": "103", "status": "Open", "description": "Specialty espresso drinks, iced cold brew, fresh pastries, and study booths."},
            {"name": "Sunset Terrace Outdoor Dining", "type": "Dining Area", "floor": 2, "room_number": "201", "status": "Available", "description": "Outdoor patio dining with panoramic campus quad views."}
        ]
    },
    {
        "name": "Innovation & Tech Incubator",
        "code": "INO",
        "category": "Academic",
        "description": "Next-generation center for student entrepreneurship, patent acceleration, rapid 3D prototyping, and venture capital demo days.",
        "floors": 3,
        "total_rooms": 28,
        "opening_hours": "08:00 AM - 10:00 PM (Daily)",
        "latitude": 37.4285,
        "longitude": -122.1670,
        "badge_color": "teal",
        "icon": "fa-lightbulb",
        "departments": [
            {"name": "Technology Transfer & Venture Office", "head_of_dept": "Valerie Vance, JD", "contact_email": "ventures@campus.edu", "phone": "+1 (555) 234-5901", "room_number": "INO-201"},
            {"name": "Entrepreneurship & Startup Accelerator", "head_of_dept": "Kenji Sato", "contact_email": "accelerator@campus.edu", "phone": "+1 (555) 234-5902", "room_number": "INO-210"}
        ],
        "facilities": [
            {"name": "Rapid Prototyping & 3D MakerSpace", "type": "MakerSpace", "floor": 1, "room_number": "102", "status": "Open", "description": "Laser cutters, SLA/FDM 3D printers, CNC mills, and electronics soldering stations."},
            {"name": "Venture Demo Auditorium", "type": "Auditorium", "floor": 2, "room_number": "205", "status": "Available", "description": "120-seat tiered theater equipped for startup pitches and investor panels."},
            {"name": "Startup Team Incubator Pods", "type": "Study Room", "floor": 3, "room_number": "301-308", "status": "Open", "description": "Private project rooms assigned to student founders building active ventures."}
        ]
    },
    {
        "name": "Campus Main Gate & Visitor Welcome Center",
        "code": "GATE",
        "category": "Administrative",
        "description": "Primary southern entry gate for the campus, featuring campus police dispatch, visitor registration, parking passes, and shuttle transfer stop.",
        "floors": 1,
        "total_rooms": 8,
        "opening_hours": "Open 24/7 (Security Staffed)",
        "latitude": 37.4250,
        "longitude": -122.1700,
        "badge_color": "slate",
        "icon": "fa-shield-halved",
        "departments": [
            {"name": "Campus Safety & Security Department", "head_of_dept": "Chief Robert Briggs", "contact_email": "security@campus.edu", "phone": "+1 (555) 234-5950", "room_number": "GATE-101"},
            {"name": "Visitor Information & Parking Services", "head_of_dept": "Laura Chen", "contact_email": "parking@campus.edu", "phone": "+1 (555) 234-5951", "room_number": "GATE-102"}
        ],
        "facilities": [
            {"name": "Visitor Check-in & Security Dispatch", "type": "Service", "floor": 1, "room_number": "101", "status": "Open", "description": "Guest registration, vehicle permits, and campus emergency assistance."},
            {"name": "Campus Shuttle Transit Pavilion", "type": "Transit", "floor": 1, "room_number": "Bay-A", "status": "Open", "description": "Boarding terminal for cross-campus loops and regional commuter buses."}
        ]
    },
    {
        "name": "University Grand Auditorium & Performing Arts Center",
        "code": "AUD",
        "category": "Student Life",
        "description": "A premier 1,200-seat multi-tier auditorium for university convocation, commencement ceremonies, guest lectures, and music concerts.",
        "floors": 2,
        "total_rooms": 14,
        "opening_hours": "08:00 AM - 10:00 PM (Event Scheduled)",
        "latitude": 37.4258,
        "longitude": -122.1692,
        "badge_color": "purple",
        "icon": "fa-masks-theater",
        "departments": [
            {"name": "Performing Arts & Concert Hall Management", "head_of_dept": "Prof. Victoria Sterling", "contact_email": "events@campus.edu", "phone": "+1 (555) 234-5960", "room_number": "AUD-101"}
        ],
        "facilities": [
            {"name": "Main Hall & Orchestra Concert Stage", "type": "Auditorium", "floor": 1, "room_number": "Stage-1", "status": "Open", "description": "Acoustically tuned 1,200-seat auditorium with professional digital lighting."},
            {"name": "Campus Ticket & Box Office", "type": "Service", "floor": 1, "room_number": "Box-1", "status": "Open", "description": "Student tickets for drama productions, visiting speakers, and concerts."}
        ]
    },
    {
        "name": "Falcon Student Hostel & Residential Quad",
        "code": "HST",
        "category": "Student Life",
        "description": "Four-story modern undergraduate and graduate residence halls featuring community dining commons, laundry hubs, and resident tutor suites.",
        "floors": 4,
        "total_rooms": 120,
        "opening_hours": "Open 24/7 (Resident Keycard Access)",
        "latitude": 37.4292,
        "longitude": -122.1675,
        "badge_color": "rose",
        "icon": "fa-bed",
        "departments": [
            {"name": "Residential Life & Housing Operations", "head_of_dept": "Director Chloe Anderson", "contact_email": "housing@campus.edu", "phone": "+1 (555) 234-5970", "room_number": "HST-101"}
        ],
        "facilities": [
            {"name": "Hostel Community Lounge & Study Pods", "type": "Study Room", "floor": 1, "room_number": "105", "status": "Available", "description": "Quiet study lounges, group presentation rooms, and student kitchenettes."},
            {"name": "Resident Laundry & Services Center", "type": "Service", "floor": 1, "room_number": "112", "status": "Open", "description": "Card-operated high-efficiency washers and dryers."}
        ]
    }
]

# Pathways (Edges) connecting buildings in the campus graph
# Specified by building codes: (from_code, to_code, distance_meters, pathway_name)
CAMPUS_PATHWAYS = [
    # Main Gate connections
    ("GATE", "LIB", 205.0, "South Palm Walkway"),
    ("GATE", "AUD", 115.0, "Main Gateway Promenade"),
    ("GATE", "STU", 185.0, "Southern Quad Path"),
    ("GATE", "ADM", 210.0, "West Perimeter Walkway"),

    # Auditorium connections
    ("AUD", "STU", 80.0, "Memorial Plaza Walkway"),
    ("AUD", "DINE", 115.0, "East Esplanade"),

    # Student Union connections
    ("STU", "LIB", 135.0, "Central Quad Pathway"),
    ("STU", "ENG", 125.0, "Engineering Crossway"),
    ("STU", "DINE", 95.0, "Dining Arcade Walk"),

    # Canteen connections
    ("DINE", "MAT", 90.0, "Science Concourse South"),
    ("DINE", "ENG", 170.0, "Central Quad Connector"),

    # Library connections
    ("LIB", "ADM", 160.0, "Administration Way"),
    ("LIB", "ENG", 105.0, "Technology Mall Walkway"),
    ("LIB", "HLS", 250.0, "Northwest Academic Path"),

    # Administration Center connections
    ("ADM", "ARC", 400.0, "West Campus Corridor"),

    # Computer Science & Engineering (Turing) connections
    ("ENG", "SCI", 130.0, "Discovery Way"),
    ("ENG", "MAT", 175.0, "STEM Link Walkway"),
    ("ENG", "INO", 260.0, "Founder's Way"),
    ("ENG", "HLS", 215.0, "Bioengineering Walk"),

    # Academic Block (Franklin Science) connections
    ("SCI", "INO", 135.0, "Research Park Connector"),
    ("SCI", "HST", 145.0, "North Quad Pathway"),
    ("SCI", "HLS", 250.0, "Interdisciplinary Trail"),

    # Math Tower connections
    ("MAT", "INO", 180.0, "Tech Boulevard"),

    # Innovation Incubator connections
    ("INO", "HST", 90.0, "East Residential Trail"),

    # Hostel connections
    ("HST", "ARC", 480.0, "Varsity Walkway"),

    # Health Sciences connections
    ("HLS", "ARC", 165.0, "Falcon Way North")
]


def seed_database():
    """Initializes tables and seeds initial campus dataset and pathways graph."""
    print("Initializing database schema...")
    init_db()

    conn = get_db_connection()
    try:
        # Reset tables for clean seed
        conn.execute("DELETE FROM pathways")
        conn.execute("DELETE FROM facilities")
        conn.execute("DELETE FROM departments")
        conn.execute("DELETE FROM buildings")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('buildings', 'departments', 'facilities', 'pathways')")
        conn.commit()

        print(f"Seeding {len(BUILDINGS_DATA)} campus buildings...")
        building_code_to_id = {}

        for b in BUILDINGS_DATA:
            cur = conn.execute("""
                INSERT INTO buildings (name, code, category, description, floors, total_rooms, opening_hours, latitude, longitude, badge_color, icon)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                b["name"], b["code"], b["category"], b["description"],
                b["floors"], b["total_rooms"], b["opening_hours"],
                b["latitude"], b["longitude"], b["badge_color"], b["icon"]
            ))
            building_id = cur.lastrowid
            building_code_to_id[b["code"]] = building_id

            for d in b.get("departments", []):
                conn.execute("""
                    INSERT INTO departments (name, building_id, head_of_dept, contact_email, phone, room_number)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    d["name"], building_id, d.get("head_of_dept"),
                    d.get("contact_email"), d.get("phone"), d.get("room_number")
                ))

            for f in b.get("facilities", []):
                conn.execute("""
                    INSERT INTO facilities (name, building_id, type, floor, room_number, status, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    f["name"], building_id, f["type"], f["floor"],
                    f.get("room_number"), f.get("status", "Open"), f.get("description")
                ))

        print(f"Seeding {len(CAMPUS_PATHWAYS)} campus pathways for Dijkstra pathfinding...")
        for from_code, to_code, dist, path_name in CAMPUS_PATHWAYS:
            u = building_code_to_id.get(from_code)
            v = building_code_to_id.get(to_code)
            if u and v:
                conn.execute("""
                    INSERT INTO pathways (from_building_id, to_building_id, distance_meters, pathway_name, is_accessible)
                    VALUES (?, ?, ?, ?, 1)
                """, (u, v, dist, path_name))

        conn.commit()
        print("Database seeded successfully!")

        # Print summary
        b_cnt = conn.execute("SELECT COUNT(*) FROM buildings").fetchone()[0]
        d_cnt = conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0]
        f_cnt = conn.execute("SELECT COUNT(*) FROM facilities").fetchone()[0]
        p_cnt = conn.execute("SELECT COUNT(*) FROM pathways").fetchone()[0]
        print(f"Summary: {b_cnt} Buildings, {d_cnt} Departments, {f_cnt} Facilities, {p_cnt} Pathways populated.")

    finally:
        conn.close()


if __name__ == "__main__":
    seed_database()
