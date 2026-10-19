# Smart Campus Navigator 🧭🏫

A modern, responsive, and intelligent web application designed for university campus wayfinding, academic directory exploration, shortest-path facility navigation, and AI campus assistance.

Built with **HTML5, CSS3, ES6 JavaScript, Python Flask, SQLite, and Leaflet.js with OpenStreetMap**.

---

## 📸 Overview & Features

### Step 1: Foundational Platform & Directory
1. **Modern Collegiate UI & Responsive Design**
   - Professional theme with deep slate, indigo, and emerald accents.
   - Fluid responsive layout optimized for mobile, tablet, and desktop viewports.
   - Polished typography using Google Fonts (*Outfit* and *Plus Jakarta Sans*) with FontAwesome 6 icons.
2. **Campus Navigation Bar**
   - **Home**: Hero search, live metrics dashboard, and campus directory cards.
   - **Campus Map**: Interactive map with real-time route pathfinding.
   - **AI Assistant**: Natural language assistant answering questions and calculating routes.
   - **Explore Campus**: Directory of buildings with category filters.
   - **About**: Architecture overview, database metrics, roadmap, and REST API documentation.
3. **Live Metrics Dashboard**
   - Real-time summary cards displaying counts for Campus Buildings, Academic Departments, Specialized Facilities, and Total Rooms.
4. **Multi-Entity Search Engine**
   - Debounced instant search bar with live auto-suggest dropdown matching buildings, departments, and room numbers.
5. **Dynamic Category Filtering**
   - Filter pills for *Academic*, *Administrative*, *Library*, *Student Life*, *Sports*, and *Dining*.
6. **Interactive Building Detail Modal**
   - Displays floor counts, operating hours, full descriptions, list of housed departments with contacts, and registered rooms with status badges.

### Step 2: Interactive Campus Map & Shortest Path Navigation
1. **Interactive Leaflet.js Map & OpenStreetMap Tiles**
   - Zero paid APIs or API keys required; runs on open OpenStreetMap tiles.
   - Responsive map container centered on the university campus.
2. **All Key Campus Locations & Landmarks**
   - Includes **Main Gate**, **Academic Block**, **Library**, **Computer Science Department**, **Canteen**, **Auditorium**, and **Hostel**, plus Administrative, Sports, and Research complexes.
3. **Custom Interactive Map Markers & Popups**
   - Color-coded pin markers matching each location's category with FontAwesome icons.
   - Informative popups with building metadata and quick-action buttons:
     - `Set as Start`: One-click sets the location as the navigation starting point.
     - `Set Destination`: One-click sets the location as the navigation destination.
4. **Dijkstra's Shortest Path Algorithm in Python (`pathfinding.py`)**
   - Min-heap priority queue implementation calculating the mathematically optimal walking route.
   - Realistic ground walkway distances in meters between interconnected campus nodes.
5. **Visual Polyline Highlighting & Animated Pins**
   - Renders the calculated shortest route directly on the map as an indigo polyline with an ambient glow layer.
   - Start (`START`) and Destination (`DEST`) markers with automatic map viewport auto-fitting (`fitBounds`).
6. **Route Distance & Estimated Walking Time**
   - Displays total distance (in meters) and estimated walking time (in minutes, assuming standard walking speed of ~80 m/min).
7. **Step-by-Step Turn-by-Turn Guidance**
   - Detailed navigational itinerary breaking down each walkway segment and landmark along the way.
8. **Map Search & Auto-Focus**
   - Find any landmark by name or code to smoothly fly the map camera and open its marker popup.

### Step 3: AI Campus Assistant (New!)
1. **Natural Language Campus Understanding (`assistant.py`)**
   - Rule-based natural language processing engine running 100% locally with zero external API dependencies or fees.
   - Queries answered against the SQLite database with token-based entity matching.
2. **Supported Query Categories**:
   - **Landmark Locations**: *"Where is the library?"*, *"Find the canteen"*, *"Where is the hostel?"*, *"Where is the auditorium?"*
   - **Navigation & Directions**: *"Directions from Main Gate to Computer Science"*, *"How to go from Library to Canteen"*
   - **Wayfinding Guidance**: *"How can I reach the academic block?"* (Prompts user for starting location with interactive quick-start chips)
   - **Specialized Facilities & Labs**: *"Where is the robotics lab?"*, *"Where is the student clinic?"*, *"MakerSpace"*
   - **Departments & Faculty**: *"Who is the head of computer science?"*, *"Admissions department contact"*
   - **Operating Hours**: *"What time does the library close?"*, *"Canteen hours"*
3. **Conversational Chat Interface (`/assistant`)**
   - Responsive message stream with user & assistant avatars.
   - Interactive prompt suggestion chips for quick one-click asking.
   - Animated typing indicator when searching the directory.
   - Direct action buttons (e.g. *"Open Route on Map"*, *"View on Campus Map"*).
   - Chat reset/clear functionality.
4. **Graceful Error Handling & Fallback**
   - Polite fallback explaining available query types with suggestion chips when questions cannot be resolved.
   - Input validation returning clear feedback for empty or invalid payloads.

---

## 📂 Project Structure

```
smart-campus-navigator/
├── app.py                 # Flask server, page routes, and REST API endpoints
├── assistant.py           # [Step 3] Rule-based NLP campus query resolution engine
├── database.py            # SQLite database connection, queries, and graph loader
├── pathfinding.py         # Dijkstra shortest-path algorithm & route generator
├── schema.sql             # SQL schema for buildings, departments, facilities, pathways
├── seed_data.py           # Realistic campus dataset & walkway graph seeder
├── test_app.py            # 24 automated unit tests covering all features
├── requirements.txt       # Python dependencies (Flask >= 3.0.0)
├── README.md              # Project documentation and setup instructions
├── static/
│   ├── css/
│   │   └── style.css      # Custom collegiate stylesheet with map & chat layout
│   └── js/
│       ├── app.js         # Debounced search, filtering, and modal controller
│       ├── map.js         # Leaflet controller, custom pins, search focus, and route drawing
│       └── assistant.js   # [Step 3] Chat controller, prompt chips, and message stream
└── templates/
    ├── base.html          # Base layout with navbar, footer, and modals
    ├── index.html         # Homepage: Hero search, metrics, and cards
    ├── map.html           # Interactive map page with sidebar routing panel
    ├── assistant.html     # [Step 3] Modern AI Assistant chat interface
    └── about.html         # About page with roadmap and API documentation
```

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- **Python 3.10+** installed on your system.

### 2. Open Terminal in Project Directory
```powershell
cd c:\Users\chatu\Desktop\smart-campus-navigator
```

### 3. Activate Virtual Environment
**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```
*(In standard CMD, run `venv\Scripts\activate.bat`)*

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Initialize and Seed the Database
```powershell
python seed_data.py
```

### 6. Run the Complete Test Suite (24 Tests)
```powershell
python test_app.py
```

### 7. Run the Application
```powershell
python app.py
```

### 8. Access in Browser
- **Campus AI Assistant**: 👉 **[http://127.0.0.1:5000/assistant](http://127.0.0.1:5000/assistant)**
- **Interactive Campus Map**: [http://127.0.0.1:5000/map](http://127.0.0.1:5000/map)
- **Homepage Directory**: [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **About Page**: [http://127.0.0.1:5000/about](http://127.0.0.1:5000/about)

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/stats` | Returns total counts of buildings, departments, facilities, and rooms |
| `GET` | `/api/categories` | Returns distinct building categories with counts |
| `GET` | `/api/buildings` | Returns all buildings (optional query param `?category=...`) |
| `GET` | `/api/buildings/<id>` | Returns building details with departments and facilities |
| `GET` | `/api/search?q=<query>` | Instant multi-entity search across buildings, rooms, and departments |
| `GET` | `/api/locations` | Returns all map landmarks with coordinates, icons, and badge colors |
| `GET` | `/api/route?from=<id>&to=<id>` | Computes Dijkstra shortest path, distance, walking time, and steps |
| `POST` | `/api/assistant/chat` | Natural language campus query processing with JSON payload `{ "message": "..." }` |

---

## 🗺️ Project Roadmap

- [x] **Step 1 (Completed)**: Responsive Homepage, Navigation, Dashboard Metrics, Search Bar UI, SQLite Database, and Flask Backend.
- [x] **Step 2 (Completed)**: Leaflet.js Interactive Campus Map, OpenStreetMap Tiles, Clickable Markers, Building Focus Search, and Dijkstra Shortest-Path Wayfinding.
- [x] **Step 3 (Completed)**: AI Campus Assistant with Rule-Based Natural Language Understanding, Navigation Query Integration, and Responsive Chat Interface.
- [ ] **Step 4**: Multi-Floor Indoor Maps & Administrative Management Portal.
