"""
Automated tests for Smart Campus Navigator Admin Panel.
Covers:
- Admin Authentication (login, logout, session security, password hashing)
- Protected Admin Routes (access control)
- Dashboard Statistics & Telemetry
- Building CRUD Operations (Create, Read, Update, Delete)
- Form Validation & CSRF Protection
- Regression tests for public features
"""
import unittest
import json
import re
import os
from app import app
from database import (
    get_db_connection,
    get_building_by_id,
    get_building_by_code,
    get_admin_by_username,
    create_admin_user,
    verify_admin_password,
    get_admin_dashboard_stats
)


def extract_csrf_token(response_data: bytes) -> str:
    """Helper to extract CSRF token from HTML response."""
    html = response_data.decode('utf-8', errors='ignore')
    match = re.search(r'name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']', html)
    if not match:
        match = re.search(r'value=["\']([^"\']+)["\'][^>]*name=["\']csrf_token["\']', html)
    if not match:
        match = re.search(r'id=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']', html)
    return match.group(1) if match else ""


class AdminPanelTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # Ensure a known test administrator exists
        self.test_username = "test_admin"
        self.test_password = "SecurePassword123!"
        existing = get_admin_by_username(self.test_username)
        if not existing:
            create_admin_user(self.test_username, self.test_password, "testadmin@campus.edu")

    def login_test_admin(self):
        """Helper to log in as the test admin with CSRF token."""
        resp = self.app.get('/admin/login')
        csrf_token = extract_csrf_token(resp.data)
        login_resp = self.app.post('/admin/login', data={
            'csrf_token': csrf_token,
            'username': self.test_username,
            'password': self.test_password
        }, follow_redirects=True)
        return login_resp

    # =========================================================================
    # 1. Authentication & Session Security Tests
    # =========================================================================

    def test_admin_login_page_renders(self):
        """Test GET /admin/login renders login page with CSRF token and inputs."""
        response = self.app.get('/admin/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Campus Administrator Portal', response.data)
        self.assertIn(b'csrf_token', response.data)
        self.assertIn(b'username', response.data)
        self.assertIn(b'password', response.data)

    def test_admin_login_invalid_password(self):
        """Test POST /admin/login with wrong password fails and flashes error."""
        resp = self.app.get('/admin/login')
        csrf_token = extract_csrf_token(resp.data)

        response = self.app.post('/admin/login', data={
            'csrf_token': csrf_token,
            'username': self.test_username,
            'password': 'WrongPassword999!'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid administrator username or password', response.data)
        with self.app.session_transaction() as sess:
            self.assertNotIn('admin_id', sess)

    def test_admin_login_nonexistent_user(self):
        """Test POST /admin/login with non-existent username fails."""
        resp = self.app.get('/admin/login')
        csrf_token = extract_csrf_token(resp.data)

        response = self.app.post('/admin/login', data={
            'csrf_token': csrf_token,
            'username': 'ghost_user_xyz',
            'password': 'AnyPassword123!'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid administrator username or password', response.data)

    def test_admin_login_success(self):
        """Test POST /admin/login with correct credentials authenticates and creates session."""
        response = self.login_test_admin()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Campus Operations Dashboard', response.data)
        self.assertIn(b'Secure Session', response.data)

        with self.app.session_transaction() as sess:
            self.assertIn('admin_id', sess)
            self.assertEqual(sess.get('admin_username'), self.test_username)

    def test_admin_logout(self):
        """Test GET /admin/logout clears admin session and redirects to login."""
        self.login_test_admin()
        response = self.app.get('/admin/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have been signed out safely', response.data)

        with self.app.session_transaction() as sess:
            self.assertNotIn('admin_id', sess)

    def test_protected_routes_unauthenticated_redirect(self):
        """Test accessing admin routes while unauthenticated redirects to /admin/login."""
        protected_urls = [
            '/admin',
            '/admin/dashboard',
            '/admin/buildings',
            '/admin/buildings/new',
            '/admin/buildings/1',
            '/admin/buildings/1/edit'
        ]
        for url in protected_urls:
            response = self.app.get(url, follow_redirects=False)
            self.assertEqual(response.status_code, 302, f"Failed for {url}")
            self.assertIn('/admin/login', response.headers.get('Location', ''))

    def test_password_hashing_security(self):
        """Test that passwords are stored as PBKDF2/scrypt hashes and never in plain text."""
        custom_user = "hash_verify_user"
        custom_pass = "SuperSecretHash2026!"
        existing = get_admin_by_username(custom_user)
        if not existing:
            user_id = create_admin_user(custom_user, custom_pass, "hash@campus.edu")
        else:
            user_id = existing['id']

        user = get_admin_by_username(custom_user)
        self.assertIsNotNone(user)
        self.assertNotEqual(user['password_hash'], custom_pass)
        self.assertTrue(user['password_hash'].startswith('scrypt:') or user['password_hash'].startswith('pbkdf2:'))
        self.assertTrue(verify_admin_password(user['password_hash'], custom_pass))
        self.assertFalse(verify_admin_password(user['password_hash'], "WrongPassword"))

    # =========================================================================
    # 2. Dashboard Statistics Tests
    # =========================================================================

    def test_admin_dashboard_metrics(self):
        """Test admin dashboard statistics display accurate campus telemetry."""
        self.login_test_admin()
        response = self.app.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)

        # Check key stat values match database
        db_stats = get_admin_dashboard_stats()
        self.assertIn(str(db_stats['total_buildings']).encode(), response.data)
        self.assertIn(str(db_stats['total_departments']).encode(), response.data)
        self.assertIn(str(db_stats['total_facilities']).encode(), response.data)
        self.assertIn(b'Category Distribution', response.data)
        self.assertIn(b'Recent Campus Buildings', response.data)

    # =========================================================================
    # 3. Building CRUD Operations Tests
    # =========================================================================

    def test_admin_buildings_list_and_filter(self):
        """Test GET /admin/buildings loads management table and category filtering."""
        self.login_test_admin()
        response = self.app.get('/admin/buildings')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Campus Buildings Directory', response.data)
        self.assertIn(b'Turing Hall', response.data)

        # Filter by Academic
        cat_resp = self.app.get('/admin/buildings?category=Academic')
        self.assertEqual(cat_resp.status_code, 200)
        self.assertIn(b'Turing Hall', cat_resp.data)

        # Search query
        search_resp = self.app.get('/admin/buildings?q=Library')
        self.assertEqual(search_resp.status_code, 200)
        self.assertIn(b'Central Memorial Library', search_resp.data)

    def test_admin_building_view_detail(self):
        """Test GET /admin/buildings/<id> renders full building specifications."""
        self.login_test_admin()
        response = self.app.get('/admin/buildings/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Landmark Profile', response.data)
        self.assertIn(b'Turing Hall', response.data)
        self.assertIn(b'Computer Science &amp; Engineering', response.data)
        self.assertIn(b'Navigation Coordinates', response.data)

    def test_admin_add_building_flow(self):
        """Test adding a new building with validation, persistence, and uniqueness."""
        self.login_test_admin()

        # 1. GET form
        form_resp = self.app.get('/admin/buildings/new')
        self.assertEqual(form_resp.status_code, 200)
        csrf_token = extract_csrf_token(form_resp.data)
        self.assertTrue(bool(csrf_token))

        # 2. POST valid building data
        test_code = "TST99"
        # Ensure code doesn't exist before test
        existing = get_building_by_code(test_code)
        if existing:
            conn = get_db_connection()
            conn.execute("DELETE FROM buildings WHERE code = ?", (test_code,))
            conn.commit()
            conn.close()

        post_data = {
            'csrf_token': csrf_token,
            'name': 'Quantum Nanotechnology Research Center',
            'code': test_code,
            'category': 'Academic',
            'description': 'Advanced cleanrooms, cryogenics, and quantum computing labs.',
            'floors': '4',
            'total_rooms': '36',
            'opening_hours': '08:00 AM - 10:00 PM (Daily)',
            'latitude': '37.4290',
            'longitude': '-122.1675',
            'badge_color': 'teal',
            'icon': 'fa-atom'
        }

        add_resp = self.app.post('/admin/buildings/new', data=post_data, follow_redirects=True)
        self.assertEqual(add_resp.status_code, 200)
        self.assertIn(b'Quantum Nanotechnology Research Center', add_resp.data)
        self.assertIn(b'successfully created', add_resp.data)

        # 3. Verify in database
        created = get_building_by_code(test_code)
        self.assertIsNotNone(created)
        self.assertEqual(created['name'], 'Quantum Nanotechnology Research Center')
        self.assertEqual(created['floors'], 4)
        self.assertEqual(created['total_rooms'], 36)

        # 4. Verify duplicate code error
        dup_resp = self.app.post('/admin/buildings/new', data=post_data, follow_redirects=True)
        self.assertEqual(dup_resp.status_code, 200)
        self.assertIn(b'already assigned', dup_resp.data)

    def test_admin_add_building_validation_errors(self):
        """Test form validation errors on invalid building submission."""
        self.login_test_admin()
        form_resp = self.app.get('/admin/buildings/new')
        csrf_token = extract_csrf_token(form_resp.data)

        # Submit empty name and invalid floors
        invalid_data = {
            'csrf_token': csrf_token,
            'name': '',
            'code': 'X',  # Too short (min 2 chars)
            'category': 'Academic',
            'floors': '0',  # Min is 1
            'total_rooms': '-5'  # Min is 1
        }
        resp = self.app.post('/admin/buildings/new', data=invalid_data, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Building name is required', resp.data)
        self.assertIn(b'must be between 2 and 10 characters', resp.data)

    def test_admin_edit_building_flow(self):
        """Test editing an existing building and verifying updated values."""
        self.login_test_admin()

        # First create a temporary building to edit
        new_code = "EDIT1"
        existing = get_building_by_code(new_code)
        if not existing:
            resp = self.app.get('/admin/buildings/new')
            csrf = extract_csrf_token(resp.data)
            self.app.post('/admin/buildings/new', data={
                'csrf_token': csrf,
                'name': 'Pre-Edit Building',
                'code': new_code,
                'category': 'Services',
                'floors': '2',
                'total_rooms': '12',
                'badge_color': 'slate',
                'icon': 'fa-wrench'
            })
            b_record = get_building_by_code(new_code)
        else:
            b_record = existing

        # GET edit form
        edit_get = self.app.get(f'/admin/buildings/{b_record["id"]}/edit')
        self.assertEqual(edit_get.status_code, 200)
        csrf_token = extract_csrf_token(edit_get.data)

        # POST update
        updated_data = {
            'csrf_token': csrf_token,
            'name': 'Post-Edit Building Renamed',
            'code': new_code,
            'category': 'Academic',
            'description': 'Updated description for testing.',
            'floors': '5',
            'total_rooms': '50',
            'opening_hours': '24/7 Access',
            'latitude': '37.4280',
            'longitude': '-122.1690',
            'badge_color': 'purple',
            'icon': 'fa-graduation-cap'
        }

        edit_post = self.app.post(f'/admin/buildings/{b_record["id"]}/edit', data=updated_data, follow_redirects=True)
        self.assertEqual(edit_post.status_code, 200)
        self.assertIn(b'updated successfully', edit_post.data)

        # Verify in database
        refreshed = get_building_by_id(b_record['id'])
        self.assertEqual(refreshed['name'], 'Post-Edit Building Renamed')
        self.assertEqual(refreshed['floors'], 5)
        self.assertEqual(refreshed['total_rooms'], 50)

    def test_admin_delete_building_flow(self):
        """Test deleting a building via CSRF-protected endpoint."""
        self.login_test_admin()

        # Create a building dedicated to deletion
        del_code = "DEL99"
        resp = self.app.get('/admin/buildings/new')
        csrf = extract_csrf_token(resp.data)
        self.app.post('/admin/buildings/new', data={
            'csrf_token': csrf,
            'name': 'Temporary Deletion Target',
            'code': del_code,
            'category': 'Services',
            'floors': '1',
            'total_rooms': '4',
            'badge_color': 'rose',
            'icon': 'fa-trash'
        })
        b_target = get_building_by_code(del_code)
        self.assertIsNotNone(b_target)

        # POST to delete endpoint with CSRF token
        del_get = self.app.get(f'/admin/buildings/{b_target["id"]}')
        del_csrf = extract_csrf_token(del_get.data)

        del_resp = self.app.post(f'/admin/buildings/{b_target["id"]}/delete', data={
            'csrf_token': del_csrf
        }, follow_redirects=True)

        self.assertEqual(del_resp.status_code, 200)
        self.assertIn(b'deleted', del_resp.data)

        # Verify removed from database
        self.assertIsNone(get_building_by_id(b_target['id']))
        self.assertIsNone(get_building_by_code(del_code))

    # =========================================================================
    # 4. CSRF Protection Security Tests
    # =========================================================================

    def test_csrf_protection_rejects_missing_token(self):
        """Test that POST requests without CSRF token are blocked."""
        # 1. Login without CSRF
        no_csrf_login = self.app.post('/admin/login', data={
            'username': self.test_username,
            'password': self.test_password
        })
        self.assertEqual(no_csrf_login.status_code, 400)

        # 2. Add building without CSRF while logged in
        self.login_test_admin()
        no_csrf_add = self.app.post('/admin/buildings/new', data={
            'name': 'Hacker Building',
            'code': 'HACK',
            'category': 'Academic'
        })
        self.assertEqual(no_csrf_add.status_code, 400)

    def test_api_assistant_chat_remains_exempt_from_csrf(self):
        """Test that public JSON chat endpoint works without CSRF (backward compatibility)."""
        response = self.app.post('/api/assistant/chat',
                                 data=json.dumps({"message": "Hello"}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])


if __name__ == '__main__':
    unittest.main()
