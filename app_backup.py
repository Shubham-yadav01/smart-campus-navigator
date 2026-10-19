import os
from flask import Flask, render_template, request, jsonify, abort
from database import (
    DB_FILE,
    init_db,
    get_all_buildings,
    get_building_by_id,
    get_categories,
    get_campus_stats,
    search_campus,
    get_all_locations,
    get_pathways
)
from seed_data import seed_database
from pathfinding import find_shortest_path
from assistant import process_assistant_message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart-campus-dev-key-2026'

# Ensure the database exists and has seed data upon startup
def ensure_database_ready():
    if not os.path.exists(DB_FILE):
        print("Database file not found. Auto-seeding initial campus data...")
        seed_database()
    else:
        init_db()

ensure_database_ready()


@app.route('/')
def home():
    """Homepage: provides initial campus stats, category filters, and building cards."""
    category = request.args.get('category', 'all')
    buildings = get_all_buildings(category=category if category != 'all' else None)
    categories = get_categories()
    stats = get_campus_stats()
    return render_template(
        'index.html',
        buildings=buildings,
        categories=categories,
        stats=stats,
        current_category=category
    )


@app.route('/about')
def about():
    """About page: information about Smart Campus Navigator, campus overview, and architecture."""
    stats = get_campus_stats()
    return render_template('about.html', stats=stats)


@app.route('/map')
def map_view():
    """Interactive Campus Map & Shortest Path Navigation page."""
    locations = get_all_locations()
    stats = get_campus_stats()
    return render_template('map.html', locations=locations, stats=stats)


@app.route('/assistant')
def assistant_view():
    """AI Campus Assistant chat interface page."""
    stats = get_campus_stats()
    return render_template('assistant.html', stats=stats)


# ---------------- REST API Endpoints ---------------- #

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Returns campus metrics (total buildings, departments, facilities, rooms)."""
    return jsonify(get_campus_stats())


@app.route('/api/categories', methods=['GET'])
def api_categories():
    """Returns distinct building categories and counts."""
    return jsonify(get_categories())


@app.route('/api/buildings', methods=['GET'])
def api_buildings():
    """Returns list of buildings, optionally filtered by category query parameter."""
    category = request.args.get('category')
    buildings = get_all_buildings(category=category)
    return jsonify(buildings)


@app.route('/api/buildings/<int:building_id>', methods=['GET'])
def api_building_detail(building_id: int):
    """Returns detailed information for a single building, including its departments and facilities."""
    building = get_building_by_id(building_id)
    if not building:
        return jsonify({"error": "Building not found"}), 404
    return jsonify(building)


@app.route('/api/search', methods=['GET'])
def api_search():
    """
    Unified search endpoint.
    Query parameter: ?q=<search term>
    Returns matches across buildings, departments, and facilities/rooms.
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({
            "query": "",
            "total_matches": 0,
            "results": {"buildings": [], "departments": [], "facilities": []}
        })

    results = search_campus(query)
    total_matches = (
        len(results.get("buildings", [])) +
        len(results.get("departments", [])) +
        len(results.get("facilities", []))
    )

    return jsonify({
        "query": query,
        "total_matches": total_matches,
        "results": results
    })


@app.route('/api/locations', methods=['GET'])
def api_locations():
    """Returns all campus locations with coordinates for map display."""
    return jsonify(get_all_locations())


@app.route('/api/route', methods=['GET'])
def api_route():
    """
    Computes shortest walking path between two campus locations using Dijkstra's algorithm.
    Query parameters:
      - from: source building/location ID (int)
      - to: destination building/location ID (int)
    """
    from_arg = request.args.get('from', '').strip()
    to_arg = request.args.get('to', '').strip()

    if not from_arg or not to_arg:
        return jsonify({
            "success": False,
            "error": "Both 'from' (source) and 'to' (destination) parameters are required."
        }), 400

    try:
        source_id = int(from_arg)
        dest_id = int(to_arg)
    except ValueError:
        return jsonify({
            "success": False,
            "error": "Location IDs for 'from' and 'to' must be valid integers."
        }), 400

    if source_id == dest_id:
        return jsonify({
            "success": False,
            "error": "Source and destination cannot be the same location."
        }), 400

    result = find_shortest_path(source_id, dest_id)
    if not result.get("success", False):
        return jsonify(result), 404

    return jsonify(result)


@app.route('/api/assistant/chat', methods=['POST'])
def api_assistant_chat():
    """
    Campus AI Assistant natural language query endpoint.
    Expects JSON: { "message": "query string" }
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Invalid request payload. Expected a JSON object with 'message'."
        }), 400

    raw_message = data.get('message', '')
    if not isinstance(raw_message, str) or not raw_message.strip():
        return jsonify({
            "success": False,
            "error": "Please provide a non-empty 'message' string."
        }), 400

    response = process_assistant_message(raw_message)
    return jsonify(response)


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Endpoint not found"}), 404
    return render_template('base.html', not_found=True), 404


@app.errorhandler(500)
def server_error(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Internal server error"}), 500
    return "<h1>500 - Internal Server Error</h1>", 500


if __name__ == '__main__':
    # Local development server
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Smart Campus Navigator at http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=True)
