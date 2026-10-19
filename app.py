import os
from functools import wraps
from flask import (
    Flask, render_template, request, jsonify, abort,
    redirect, url_for, session, flash, g
)
from flask_wtf.csrf import CSRFProtect
from forms import LoginForm, BuildingForm, DeleteBuildingForm
from database import (
    DB_FILE,
    init_db,
    get_all_buildings,
    get_building_by_id,
    get_categories,
    get_campus_stats,
    search_campus,
    get_all_locations,
    get_pathways,
    get_admin_by_username,
    get_admin_by_id,
    verify_admin_password,
    update_admin_last_login,
    ensure_default_admin,
    get_building_by_code,
    add_building,
    update_building,
    delete_building,
    get_admin_dashboard_stats
)
from seed_data import seed_database
from pathfinding import find_shortest_path
from assistant import process_assistant_message

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'smart-campus-dev-key-2026')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

csrf = CSRFProtect(app)

# Ensure the database exists and has seed data upon startup
def ensure_database_ready():
    if not os.path.exists(DB_FILE):
        print("Database file not found. Auto-seeding initial campus data...")
        seed_database()
    else:
        init_db()
    ensure_default_admin()

ensure_database_ready()


@app.before_request
def load_logged_in_admin():
    admin_id = session.get('admin_id')
    if admin_id is None:
        g.admin = None
    else:
        g.admin = get_admin_by_id(admin_id)


@app.context_processor
def inject_admin_context():
    return {
        'current_admin': getattr(g, 'admin', None),
        'is_admin_authenticated': bool(session.get('admin_id'))
    }


def admin_required(view_func):
    """Decorator ensuring that only authenticated administrators can access protected views."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'admin_id' not in session or not session.get('admin_id'):
            flash("Please sign in to access the campus administration panel.", "warning")
            return redirect(url_for('admin_login', next=request.path))
        return view_func(*args, **kwargs)
    return wrapped_view


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
@csrf.exempt
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


# ---------------- Admin Authentication & Dashboard Routes ---------------- #

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login with hashed password authentication and CSRF protection."""
    if session.get('admin_id'):
        return redirect(url_for('admin_dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        user = get_admin_by_username(username)

        if user and verify_admin_password(user['password_hash'], password):
            session.clear()
            session['admin_id'] = user['id']
            session['admin_username'] = user['username']
            update_admin_last_login(user['id'])
            flash(f"Welcome back, {user['username']}! Signed into Campus Admin Panel.", "success")

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                return redirect(next_page)
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid administrator username or password. Please verify credentials.", "danger")

    return render_template('admin/login.html', form=form)


@app.route('/admin/logout', methods=['GET', 'POST'])
def admin_logout():
    """Clears admin session and redirects to login."""
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for('admin_login'))


@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin Dashboard: statistics, category distributions, and quick actions."""
    stats = get_admin_dashboard_stats()
    delete_form = DeleteBuildingForm()
    return render_template('admin/dashboard.html', stats=stats, delete_form=delete_form)


@app.route('/admin/buildings', methods=['GET'])
@admin_required
def admin_buildings():
    """Admin Buildings Directory: table with category filter, search, and CRUD actions."""
    category = request.args.get('category', 'all')
    search_q = request.args.get('q', '').strip()

    all_buildings = get_all_buildings(category=category if category != 'all' else None)
    if search_q:
        q_lower = search_q.lower()
        buildings = [
            b for b in all_buildings
            if q_lower in b['name'].lower() or q_lower in b['code'].lower() or q_lower in b['category'].lower()
        ]
    else:
        buildings = all_buildings

    categories = get_categories()
    delete_form = DeleteBuildingForm()
    return render_template(
        'admin/buildings.html',
        buildings=buildings,
        categories=categories,
        current_category=category,
        search_q=search_q,
        delete_form=delete_form
    )


@app.route('/admin/buildings/new', methods=['GET', 'POST'])
@admin_required
def admin_building_new():
    """Add new campus building with form validation and code uniqueness verification."""
    form = BuildingForm()
    if form.validate_on_submit():
        code_clean = form.code.data.strip().upper()
        existing = get_building_by_code(code_clean)
        if existing:
            form.code.errors.append(f"Building code '{code_clean}' is already assigned to {existing['name']}.")
        else:
            building_data = {
                'name': form.name.data.strip(),
                'code': code_clean,
                'category': form.category.data,
                'description': form.description.data,
                'floors': form.floors.data,
                'total_rooms': form.total_rooms.data,
                'opening_hours': form.opening_hours.data,
                'latitude': form.latitude.data,
                'longitude': form.longitude.data,
                'badge_color': form.badge_color.data,
                'icon': form.icon.data.strip() if form.icon.data else 'fa-building'
            }
            new_id = add_building(building_data)
            flash(f"Building '{form.name.data}' ({code_clean}) successfully created!", "success")
            return redirect(url_for('admin_buildings'))

    return render_template(
        'admin/building_form.html',
        form=form,
        title="Add New Campus Building",
        action="create"
    )


@app.route('/admin/buildings/<int:building_id>', methods=['GET'])
@admin_required
def admin_building_view(building_id: int):
    """View full details of a specific campus building, departments, and facilities."""
    building = get_building_by_id(building_id)
    if not building:
        abort(404)
    delete_form = DeleteBuildingForm()
    return render_template('admin/building_view.html', building=building, delete_form=delete_form)


@app.route('/admin/buildings/<int:building_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_building_edit(building_id: int):
    """Edit existing campus building with pre-populated form and validation."""
    building = get_building_by_id(building_id)
    if not building:
        abort(404)

    if request.method == 'GET':
        form = BuildingForm(data=building)
    else:
        form = BuildingForm()

    if form.validate_on_submit():
        code_clean = form.code.data.strip().upper()
        existing = get_building_by_code(code_clean, exclude_id=building_id)
        if existing:
            form.code.errors.append(f"Building code '{code_clean}' is already assigned to {existing['name']}.")
        else:
            building_data = {
                'name': form.name.data.strip(),
                'code': code_clean,
                'category': form.category.data,
                'description': form.description.data,
                'floors': form.floors.data,
                'total_rooms': form.total_rooms.data,
                'opening_hours': form.opening_hours.data,
                'latitude': form.latitude.data,
                'longitude': form.longitude.data,
                'badge_color': form.badge_color.data,
                'icon': form.icon.data.strip() if form.icon.data else 'fa-building'
            }
            update_building(building_id, building_data)
            flash(f"Building '{form.name.data}' ({code_clean}) updated successfully!", "success")
            return redirect(url_for('admin_buildings'))

    return render_template(
        'admin/building_form.html',
        form=form,
        building=building,
        title=f"Edit Building: {building['name']}",
        action="edit"
    )


@app.route('/admin/buildings/<int:building_id>/delete', methods=['POST'])
@admin_required
def admin_building_delete(building_id: int):
    """CSRF-protected endpoint to safely delete a campus building."""
    form = DeleteBuildingForm()
    if form.validate_on_submit():
        building = get_building_by_id(building_id)
        if building:
            delete_building(building_id)
            flash(f"Building '{building['name']}' ({building['code']}) and associated records were deleted.", "success")
        else:
            flash("The specified building was not found.", "warning")
    else:
        flash("CSRF validation failed for delete operation.", "danger")
    return redirect(url_for('admin_buildings'))


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
