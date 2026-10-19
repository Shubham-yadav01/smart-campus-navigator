"""
Rule-Based AI Campus Assistant Module for Smart Campus Navigator.
Answers natural language queries about campus buildings, departments, facilities,
operating hours, and shortest-path navigation using the local SQLite database.
Requires zero paid API keys or external services.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from database import get_db_connection, get_all_locations, get_building_by_id
from pathfinding import find_shortest_path


def normalize_text(text: str) -> str:
    """Cleans and standardizes input string for keyword and regex matching."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text)


def get_building_by_keywords(query: str) -> Optional[Dict[str, Any]]:
    """
    Finds a campus building matching the query string using aliases, codes, and keywords.
    """
    clean_q = normalize_text(query)
    locations = get_all_locations()

    # Pre-defined alias map for campus landmarks
    aliases = {
        "gate": "GATE",
        "main gate": "GATE",
        "entry": "GATE",
        "entrance": "GATE",
        "welcome center": "GATE",
        "security": "GATE",
        
        "library": "LIB",
        "central library": "LIB",
        "learning commons": "LIB",
        "books": "LIB",

        "cs": "ENG",
        "computer science": "ENG",
        "computer science department": "ENG",
        "turing": "ENG",
        "turing hall": "ENG",
        "engineering": "ENG",
        "robotics": "ENG",

        "academic block": "SCI",
        "science complex": "SCI",
        "franklin": "SCI",
        "science": "SCI",

        "canteen": "DINE",
        "dining": "DINE",
        "dining hall": "DINE",
        "cafeteria": "DINE",
        "food": "DINE",
        "coffee": "DINE",

        "auditorium": "AUD",
        "grand auditorium": "AUD",
        "performing arts": "AUD",
        "theater": "AUD",
        "theatre": "AUD",

        "hostel": "HST",
        "student hostel": "HST",
        "dorm": "HST",
        "dormitory": "HST",
        "residence": "HST",
        "residential": "HST",

        "admin": "ADM",
        "administration": "ADM",
        "chancellor": "ADM",
        "admissions": "ADM",
        "financial aid": "ADM",

        "student union": "STU",
        "union": "STU",
        "student activity": "STU",
        "bookstore": "STU",

        "gym": "ARC",
        "athletics": "ARC",
        "sports": "ARC",
        "pool": "ARC",
        "swimming": "ARC",

        "health": "HLS",
        "clinic": "HLS",
        "wellness": "HLS",
        "nursing": "HLS",
        "hospital": "HLS",

        "math": "MAT",
        "mathematics": "MAT",
        "physics": "MAT",
        "newton": "MAT",

        "incubator": "INO",
        "innovation": "INO",
        "makerspace": "INO",
        "startup": "INO"
    }

    # 1. Check exact code match first
    for loc in locations:
        if loc['code'].lower() == clean_q or f" {loc['code'].lower()} " in f" {clean_q} ":
            return get_building_by_id(loc['id'])

    # 2. Check alias map sorted by alias length descending
    for alias, code in sorted(aliases.items(), key=lambda x: len(x[0]), reverse=True):
        if alias in clean_q:
            match_loc = next((l for l in locations if l['code'] == code), None)
            if match_loc:
                return get_building_by_id(match_loc['id'])

    # 3. Direct substring match on building name
    for loc in locations:
        if loc['name'].lower() in clean_q or clean_q in loc['name'].lower():
            return get_building_by_id(loc['id'])

    return None


def extract_navigation_endpoints(query: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Attempts to extract (source, destination) from navigation queries like:
    - "from X to Y"
    - "how to go from X to Y"
    - "directions from X to Y"
    - "reach Y from X"
    """
    clean_q = normalize_text(query)

    # Pattern: from X to Y
    match_from_to = re.search(r'\bfrom\s+(.+?)\s+to\s+(.+)', clean_q)
    if match_from_to:
        src_text = match_from_to.group(1).strip()
        dst_text = match_from_to.group(2).strip()
        src_building = get_building_by_keywords(src_text)
        dst_building = get_building_by_keywords(dst_text)
        if src_building and dst_building:
            return src_building, dst_building

    # Pattern: reach Y from X
    match_reach_from = re.search(r'\breach\s+(.+?)\s+from\s+(.+)', clean_q)
    if match_reach_from:
        dst_text = match_reach_from.group(1).strip()
        src_text = match_reach_from.group(2).strip()
        src_building = get_building_by_keywords(src_text)
        dst_building = get_building_by_keywords(dst_text)
        if src_building and dst_building:
            return src_building, dst_building

    # Pattern: to Y from X
    match_to_from = re.search(r'\bto\s+(.+?)\s+from\s+(.+)', clean_q)
    if match_to_from:
        dst_text = match_to_from.group(1).strip()
        src_text = match_to_from.group(2).strip()
        src_building = get_building_by_keywords(src_text)
        dst_building = get_building_by_keywords(dst_text)
        if src_building and dst_building:
            return src_building, dst_building

    return None, None


def search_facilities(query: str) -> List[Dict[str, Any]]:
    """Searches facilities table by name, type, or description with token support."""
    clean_q = normalize_text(query)
    filler = {"where", "is", "the", "find", "show", "me", "are", "there", "any", "a", "an", "at", "in", "tell", "about"}
    tokens = [w for w in clean_q.split() if w not in filler]
    if not tokens:
        return []

    conn = get_db_connection()
    try:
        # First try exact phrase
        exact_like = f"%{' '.join(tokens)}%"
        rows = conn.execute("""
            SELECT f.*, b.name as building_name, b.code as building_code, b.id as building_id
            FROM facilities f
            JOIN buildings b ON f.building_id = b.id
            WHERE f.name LIKE ? OR f.type LIKE ? OR f.description LIKE ?
            ORDER BY f.name ASC
            LIMIT 5
        """, (exact_like, exact_like, exact_like)).fetchall()
        if rows:
            return [dict(r) for r in rows]

        # Prioritize specific non-generic tokens (e.g. 'robotics' over 'lab')
        specific_tokens = [t for t in tokens if t not in {"lab", "room", "center", "hall", "facility"}]
        search_tokens = specific_tokens if specific_tokens else tokens

        conditions = " OR ".join(["(f.name LIKE ? OR f.description LIKE ? OR f.type LIKE ?)" for _ in search_tokens])
        params = []
        for t in search_tokens:
            p = f"%{t}%"
            params.extend([p, p, p])

        rows = conn.execute(f"""
            SELECT f.*, b.name as building_name, b.code as building_code, b.id as building_id
            FROM facilities f
            JOIN buildings b ON f.building_id = b.id
            WHERE {conditions}
            ORDER BY f.name ASC
            LIMIT 5
        """, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def search_departments(query: str) -> List[Dict[str, Any]]:
    """Searches departments table by department name or head of department with token support."""
    clean_q = normalize_text(query)
    filler = {"who", "is", "head", "of", "the", "department", "dept", "contact", "email", "phone", "where", "what", "find"}
    tokens = [w for w in clean_q.split() if w not in filler]
    if not tokens:
        return []

    conn = get_db_connection()
    try:
        exact_like = f"%{' '.join(tokens)}%"
        rows = conn.execute("""
            SELECT d.*, b.name as building_name, b.code as building_code, b.id as building_id
            FROM departments d
            JOIN buildings b ON d.building_id = b.id
            WHERE d.name LIKE ? OR d.head_of_dept LIKE ?
            ORDER BY d.name ASC
            LIMIT 5
        """, (exact_like, exact_like)).fetchall()
        if rows:
            return [dict(r) for r in rows]

        conditions = " OR ".join(["(d.name LIKE ? OR d.head_of_dept LIKE ?)" for _ in tokens])
        params = []
        for t in tokens:
            p = f"%{t}%"
            params.extend([p, p])

        rows = conn.execute(f"""
            SELECT d.*, b.name as building_name, b.code as building_code, b.id as building_id
            FROM departments d
            JOIN buildings b ON d.building_id = b.id
            WHERE {conditions}
            ORDER BY d.name ASC
            LIMIT 5
        """, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def process_assistant_message(message: str) -> Dict[str, Any]:
    """
    Main rule-based intent router and message processor.
    Classifies user message into one of:
    - GREETING / HELP
    - NAVIGATION_PAIR (source & destination provided -> calculated Dijkstra route)
    - NAVIGATION_SINGLE (destination provided -> asks for start point with quick chips)
    - BUILDING_LOCATION ("Where is X?", "Find X")
    - FACILITY_QUERY ("Where is the robotics lab?", "MakerSpace", "clinic")
    - DEPARTMENT_QUERY ("Who is head of CS?", "Department contact")
    - HOURS_QUERY ("What time does library open?")
    - FALLBACK (polite guidance + suggested prompts)
    """
    clean = normalize_text(message)

    if not clean:
        return {
            "success": False,
            "reply": "Please enter a question or topic so I can assist you.",
            "intent": "empty_input",
            "suggestions": ["Where is the Library?", "Find the Canteen", "How can I reach the Academic Block?"]
        }

    # 1. GREETING & GENERAL OVERVIEW
    greeting_triggers = ["hello", "hi", "hey", "help", "who are you", "what can you do", "good morning", "good afternoon"]
    if any(re.search(rf'\b{trigger}\b', clean) for trigger in greeting_triggers) and len(clean.split()) <= 4:
        return {
            "success": True,
            "intent": "greeting",
            "reply": (
                "👋 **Hello! I am your Smart Campus Assistant.**\n\n"
                "I can help you navigate the university campus, locate buildings, find classrooms and specialized labs, "
                "look up department faculty, and calculate the shortest walking routes with step-by-step guidance.\n\n"
                "**Here are a few things you can ask me:**\n"
                "• *'Where is the Library?'*\n"
                "• *'Find the Canteen'* or *'Where can I eat?'*\n"
                "• *'How can I reach the Academic Block?'*\n"
                "• *'Directions from Main Gate to Computer Science'* \n"
                "• *'Where is the Robotics Lab?'*\n"
                "• *'Who is the head of Computer Science?'*"
            ),
            "suggestions": [
                "Where is the Library?",
                "Find the Canteen",
                "How can I reach the Academic Block?",
                "Directions from Main Gate to Library",
                "Where is the Robotics Lab?"
            ]
        }

    # 2. NAVIGATION: BOTH SOURCE & DESTINATION SPECIFIED ("from X to Y")
    is_nav_query = any(word in clean for word in ["how to go", "how to reach", "directions", "how can i reach", "route", "way to", "navigate", "walk from"])
    src_building, dst_building = extract_navigation_endpoints(message)

    if src_building and dst_building:
        if src_building['id'] == dst_building['id']:
            return {
                "success": True,
                "intent": "navigation_same",
                "reply": f"📍 You are already at **{src_building['name']}**! Both your starting point and destination are the same location.",
                "suggestions": ["Where is the Library?", "Find the Canteen"]
            }

        # Calculate Dijkstra route
        route_result = find_shortest_path(src_building['id'], dst_building['id'])
        if route_result.get("success", False):
            dist = round(route_result['total_distance_meters'])
            mins = route_result['estimated_time_minutes']
            steps_list = "\n".join([f"{i+1}. {s}" for i, s in enumerate(route_result['steps'])])

            reply_text = (
                f"🚶 **Shortest Walking Route:** **{src_building['name']} ({src_building['code']})** ➔ **{dst_building['name']} ({dst_building['code']})**\n\n"
                f"• **Distance:** {dist} meters\n"
                f"• **Estimated Walk Time:** {mins} minute{'s' if mins != 1 else ''}\n"
                f"• **Waypoints:** {route_result['node_count']} landmarks\n\n"
                f"**Step-by-Step Guidance:**\n{steps_list}\n\n"
                f"🗺️ *You can also visualize this route on the interactive map!*"
            )

            return {
                "success": True,
                "intent": "navigation_pair",
                "reply": reply_text,
                "route_data": {
                    "source_id": src_building['id'],
                    "dest_id": dst_building['id'],
                    "distance_meters": dist,
                    "estimated_time_minutes": mins
                },
                "action": {
                    "type": "map_link",
                    "label": "Open Route on Map",
                    "url": f"/map?from={src_building['id']}&to={dst_building['id']}"
                },
                "suggestions": [
                    f"Tell me about {dst_building['name']}",
                    "Find the Canteen",
                    "Where is the Main Gate?"
                ]
            }

    # 3. NAVIGATION: DESTINATION ONLY ("How can I reach the academic block?")
    if is_nav_query or any(clean.startswith(prefix) for prefix in ["how can i reach", "how to reach", "directions to", "how do i get to", "way to"]):
        target_b = get_building_by_keywords(message)
        if target_b:
            return {
                "success": True,
                "intent": "navigation_single",
                "reply": (
                    f"🧭 To guide you to **{target_b['name']} ({target_b['code']})**, where are you currently located?\n\n"
                    f"Select your starting location below or type *'from [Location] to {target_b['name']}'*:"
                ),
                "target_building": {
                    "id": target_b['id'],
                    "name": target_b['name'],
                    "code": target_b['code']
                },
                "quick_starts": [
                    {"label": "From Main Gate", "query": f"Directions from Main Gate to {target_b['name']}"},
                    {"label": "From Library", "query": f"Directions from Library to {target_b['name']}"},
                    {"label": "From Hostel", "query": f"Directions from Hostel to {target_b['name']}"},
                    {"label": "From Canteen", "query": f"Directions from Canteen to {target_b['name']}"}
                ],
                "suggestions": [
                    f"Directions from Main Gate to {target_b['name']}",
                    f"Directions from Library to {target_b['name']}",
                    f"Tell me about {target_b['name']}"
                ]
            }

    # 4. OPERATING HOURS QUERIES
    if any(kw in clean for kw in ["hour", "hours", "time", "timing", "when does", "open", "close"]):
        b_match = get_building_by_keywords(message)
        if b_match:
            return {
                "success": True,
                "intent": "hours_query",
                "reply": (
                    f"🕒 **Operating Hours for {b_match['name']} ({b_match['code']}):**\n\n"
                    f"• **Schedule:** {b_match['opening_hours']}\n"
                    f"• **Category:** {b_match['category']} Complex\n"
                    f"• **Total Floors:** {b_match['floors']} | **Rooms:** {b_match['total_rooms']}\n\n"
                    f"*{b_match['description']}*"
                ),
                "suggestions": [
                    f"Where is {b_match['name']}?",
                    f"Directions from Main Gate to {b_match['name']}",
                    "What are the Library hours?"
                ]
            }

    # 5. SPECIALIZED FACILITY / LAB QUERIES
    if any(kw in clean for kw in ["lab", "facility", "room", "clinic", "makerspace", "auditorium stage", "pool", "swimming", "store", "bookstore", "esports", "studio"]):
        facilities = search_facilities(message)
        if facilities:
            f = facilities[0]
            status_emoji = "🟢" if f['status'] == 'Open' else "🟡"
            reply_text = (
                f"🔬 **Facility Found:** **{f['name']}**\n\n"
                f"• **Building:** {f['building_name']} ({f['building_code']})\n"
                f"• **Floor & Room:** Floor {f['floor']}, Room {f['room_number'] or 'Main Area'}\n"
                f"• **Type:** {f['type']}\n"
                f"• **Status:** {status_emoji} {f['status']}\n"
                f"• **Description:** {f['description'] or 'Specialized university campus facility.'}\n\n"
                f"Need directions? Ask *'How to reach {f['building_name']}?'*"
            )
            return {
                "success": True,
                "intent": "facility_info",
                "reply": reply_text,
                "action": {
                    "type": "map_link",
                    "label": f"View {f['building_code']} on Map",
                    "url": f"/map"
                },
                "suggestions": [
                    f"How can I reach {f['building_name']}?",
                    f"Tell me about {f['building_name']}",
                    "Where is the Library?"
                ]
            }

    # 6. DEPARTMENT / FACULTY HEAD QUERIES
    if any(kw in clean for kw in ["department", "dept", "head", "faculty", "email", "contact", "phone", "professor"]):
        departments = search_departments(message)
        if departments:
            d = departments[0]
            reply_text = (
                f"🎓 **Department Information:** **{d['name']}**\n\n"
                f"• **Building:** {d['building_name']} ({d['building_code']})\n"
                f"• **Department Head:** {d['head_of_dept'] or 'Department Chair'}\n"
                f"• **Office Room:** {d['room_number'] or 'Main Office'}\n"
                f"• **Contact Email:** {d['contact_email'] or 'Not listed'}\n"
                f"• **Phone:** {d['phone'] or 'Not listed'}\n\n"
                f"Ask *'How to reach {d['building_name']}?'* to get step-by-step walking directions."
            )
            return {
                "success": True,
                "intent": "department_info",
                "reply": reply_text,
                "suggestions": [
                    f"How can I reach {d['building_name']}?",
                    f"Where is {d['building_name']}?",
                    "Where is the Admissions Office?"
                ]
            }

    # 7. BUILDING / LANDMARK QUERIES ("Where is X?", "Find X", "Tell me about X")
    building = get_building_by_keywords(message)
    if building:
        dept_names = [d['name'] for d in building.get('departments', [])]
        dept_str = ", ".join(dept_names[:3]) if dept_names else "General campus operations"
        fac_count = len(building.get('facilities', []))

        reply_text = (
            f"🏛️ **{building['name']} ({building['code']})**\n\n"
            f"• **Category:** {building['category']}\n"
            f"• **Floors & Rooms:** {building['floors']} Floor{'s' if building['floors'] != 1 else ''}, {building['total_rooms']} Rooms\n"
            f"• **Operating Hours:** {building['opening_hours']}\n"
            f"• **Key Departments:** {dept_str}\n"
            f"• **Specialized Facilities:** {fac_count} registered facilities/labs\n\n"
            f"*{building['description']}*"
        )

        return {
            "success": True,
            "intent": "location_info",
            "reply": reply_text,
            "building": {
                "id": building['id'],
                "name": building['name'],
                "code": building['code']
            },
            "action": {
                "type": "map_link",
                "label": f"View {building['code']} on Map",
                "url": f"/map"
            },
            "suggestions": [
                f"How can I reach {building['name']}?",
                f"Directions from Main Gate to {building['name']}",
                "Find the Canteen",
                "Where is the Library?"
            ]
        }

    # 8. FALLBACK RESPONSE
    return {
        "success": True,
        "intent": "fallback",
        "reply": (
            "🤔 I couldn't find a direct match for that question.\n\n"
            "I can answer questions regarding:\n"
            "• **Campus Buildings:** e.g., *'Where is the Library?'*, *'Find the Canteen'*, *'Where is the Hostel?'*\n"
            "• **Shortest Path Routes:** e.g., *'How can I reach the Academic Block?'* or *'Directions from Main Gate to Computer Science'*\n"
            "• **Labs & Facilities:** e.g., *'Where is the Robotics Lab?'*, *'Where is the Clinic?'*\n"
            "• **Departments:** e.g., *'Who is the head of Computer Science?'*, *'Admissions department'*\n"
            "• **Operating Hours:** e.g., *'What are the Library hours?'*\n\n"
            "Try clicking one of the suggested prompts below!"
        ),
        "suggestions": [
            "Where is the Library?",
            "Find the Canteen",
            "How can I reach the Academic Block?",
            "Directions from Main Gate to Library",
            "Where is the Robotics Lab?"
        ]
    }
