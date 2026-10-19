"""
Test suite to verify Smart Campus Navigator routes, APIs, and database functionality.
"""
import unittest
import json
from app import app
from database import get_campus_stats, get_all_buildings, search_campus


class SmartCampusNavigatorTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_homepage_loads(self):
        """Test GET / returns 200 OK and contains brand title."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Smart Campus', response.data)
        self.assertIn(b'Navigator', response.data)
        self.assertIn(b'Turing Hall', response.data)

    def test_about_page_loads(self):
        """Test GET /about returns 200 OK."""
        response = self.app.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'About Smart Campus Navigator', response.data)
        self.assertIn(b'System Specifications', response.data)

    def test_api_stats(self):
        """Test GET /api/stats returns accurate statistics structure."""
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('total_buildings', data)
        self.assertIn('total_departments', data)
        self.assertIn('total_facilities', data)
        self.assertGreaterEqual(data['total_buildings'], 10)
        self.assertGreaterEqual(data['total_departments'], 15)
        self.assertGreaterEqual(data['total_facilities'], 25)

    def test_api_categories(self):
        """Test GET /api/categories returns categories list."""
        response = self.app.get('/api/categories')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        category_names = [c['category'] for c in data]
        self.assertIn('Academic', category_names)
        self.assertIn('Library', category_names)

    def test_api_buildings_list(self):
        """Test GET /api/buildings returns array of buildings."""
        response = self.app.get('/api/buildings')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 10)

        # Test category filter query parameter
        cat_resp = self.app.get('/api/buildings?category=Library')
        self.assertEqual(cat_resp.status_code, 200)
        cat_data = json.loads(cat_resp.data)
        self.assertEqual(len(cat_data), 1)
        self.assertEqual(cat_data[0]['code'], 'LIB')

    def test_api_building_detail(self):
        """Test GET /api/buildings/<id> returns complete details."""
        response = self.app.get('/api/buildings/1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['id'], 1)
        self.assertIn('departments', data)
        self.assertIn('facilities', data)
        self.assertGreater(len(data['departments']), 0)
        self.assertGreater(len(data['facilities']), 0)

        # Test non-existent building returns 404
        not_found_resp = self.app.get('/api/buildings/9999')
        self.assertEqual(not_found_resp.status_code, 404)

    def test_api_search(self):
        """Test GET /api/search with various queries."""
        # Search by code
        resp = self.app.get('/api/search?q=ENG')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertGreater(len(data['results']['buildings']), 0)

        # Search by department
        resp_dept = self.app.get('/api/search?q=Computer')
        self.assertEqual(resp_dept.status_code, 200)
        data_dept = json.loads(resp_dept.data)
        self.assertGreater(data_dept['total_matches'], 0)

        # Search by room / facility
        resp_fac = self.app.get('/api/search?q=Robotics')
        self.assertEqual(resp_fac.status_code, 200)
        data_fac = json.loads(resp_fac.data)
        self.assertGreater(len(data_fac['results']['facilities']), 0)

        # Empty search
        resp_empty = self.app.get('/api/search?q=')
        self.assertEqual(resp_empty.status_code, 200)
        data_empty = json.loads(resp_empty.data)
        self.assertEqual(data_empty['total_matches'], 0)

    # ---------------- Step 2 Map & Pathfinding Tests ---------------- #

    def test_map_page_loads(self):
        """Test GET /map returns 200 OK and contains Leaflet container and controls."""
        response = self.app.get('/map')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'campusMap', response.data)
        self.assertIn(b'Interactive Campus Map', response.data)
        self.assertIn(b'sourceSelect', response.data)
        self.assertIn(b'destSelect', response.data)
        self.assertIn(b'leaflet.js', response.data)

    def test_api_locations(self):
        """Test GET /api/locations returns full campus locations list with coordinates."""
        response = self.app.get('/api/locations')
        self.assertEqual(response.status_code, 200)
        locations = json.loads(response.data)
        self.assertIsInstance(locations, list)
        self.assertGreaterEqual(len(locations), 10)

        # Check required sample locations exist
        location_names = [loc['name'].lower() for loc in locations]
        self.assertTrue(any('main gate' in name for name in location_names))
        self.assertTrue(any('academic block' in name for name in location_names))
        self.assertTrue(any('library' in name for name in location_names))
        self.assertTrue(any('computer science' in name for name in location_names))
        self.assertTrue(any('canteen' in name for name in location_names))
        self.assertTrue(any('auditorium' in name for name in location_names))
        self.assertTrue(any('hostel' in name for name in location_names))

        # Check coordinates format
        for loc in locations:
            self.assertIsNotNone(loc.get('latitude'))
            self.assertIsNotNone(loc.get('longitude'))
            self.assertTrue(-90 <= loc['latitude'] <= 90)
            self.assertTrue(-180 <= loc['longitude'] <= 180)

    def test_api_route_valid(self):
        """Test GET /api/route returns shortest path between valid nodes."""
        # Find ID of Main Gate and Computer Science
        loc_resp = self.app.get('/api/locations')
        locations = json.loads(loc_resp.data)
        gate_id = next(loc['id'] for loc in locations if 'gate' in loc['name'].lower())
        cs_id = next(loc['id'] for loc in locations if 'computer science' in loc['name'].lower())

        response = self.app.get(f'/api/route?from={gate_id}&to={cs_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreater(data['total_distance_meters'], 0)
        self.assertGreaterEqual(data['estimated_time_minutes'], 1)
        self.assertGreaterEqual(len(data['coordinates']), 2)
        self.assertGreaterEqual(len(data['steps']), 2)
        self.assertEqual(data['source']['id'], gate_id)
        self.assertEqual(data['destination']['id'], cs_id)

    def test_api_route_same_source_dest(self):
        """Test GET /api/route returns 400 when source and dest are identical."""
        response = self.app.get('/api/route?from=1&to=1')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('cannot be the same', data['error'].lower())

    def test_api_route_missing_parameters(self):
        """Test GET /api/route returns 400 when from or to is missing."""
        resp1 = self.app.get('/api/route?from=1')
        self.assertEqual(resp1.status_code, 400)
        resp2 = self.app.get('/api/route?to=2')
        self.assertEqual(resp2.status_code, 400)
        resp3 = self.app.get('/api/route')
        self.assertEqual(resp3.status_code, 400)

    def test_api_route_invalid_parameter_type(self):
        """Test GET /api/route returns 400 when parameters are non-integers."""
        response = self.app.get('/api/route?from=abc&to=xyz')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_api_route_nonexistent_location(self):
        """Test GET /api/route returns 404 when location does not exist."""
        response = self.app.get('/api/route?from=9999&to=1')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    # ---------------- Step 3 AI Assistant Tests ---------------- #

    def test_assistant_page_loads(self):
        """Test GET /assistant returns 200 OK and contains chat container and prompt chips."""
        response = self.app.get('/assistant')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Campus AI Assistant', response.data)
        self.assertIn(b'chatMessages', response.data)
        self.assertIn(b'chatInput', response.data)
        self.assertIn(b'Where is the library?', response.data)

    def test_assistant_chat_greeting(self):
        """Test POST /api/assistant/chat with greeting returns greeting intent."""
        response = self.app.post('/api/assistant/chat',
                                 data=json.dumps({"message": "Hello"}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['intent'], 'greeting')
        self.assertIn('Smart Campus Assistant', data['reply'])
        self.assertGreaterEqual(len(data['suggestions']), 3)

    def test_assistant_chat_location_query(self):
        """Test POST /api/assistant/chat with 'Where is the library?' returns building info."""
        response = self.app.post('/api/assistant/chat',
                                 data=json.dumps({"message": "Where is the library?"}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['intent'], 'location_info')
        self.assertIn('LIB', data['reply'])
        self.assertIn('Library', data['reply'])

    def test_assistant_chat_navigation_single(self):
        """Test POST /api/assistant/chat with destination only prompts for starting location."""
        response = self.app.post('/api/assistant/chat',
                                 data=json.dumps({"message": "How can I reach the academic block?"}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['intent'], 'navigation_single')
        self.assertIn('quick_starts', data)
        self.assertGreaterEqual(len(data['quick_starts']), 2)

    def test_assistant_chat_navigation_pair(self):
        """Test POST /api/assistant/chat with from and to calculates Dijkstra route."""
        response = self.app.post('/api/assistant/chat',
                                 data=json.dumps({"message": "Directions from Main Gate to Library"}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['intent'], 'navigation_pair')
        self.assertIn('route_data', data)
        self.assertGreater(data['route_data']['distance_meters'], 0)
        self.assertIn('Step-by-Step Guidance', data['reply'])

    def test_assistant_chat_facility_query(self):
        """Test POST /api/assistant/chat with lab query returns facility info."""
        response = self.app.post('/api/assistant/chat',
                                 data=json.dumps({"message": "Where is the robotics lab?"}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['intent'], 'facility_info')
        self.assertIn('Robotics', data['reply'])
        self.assertIn('Turing Hall', data['reply'])

    def test_assistant_chat_department_query(self):
        """Test POST /api/assistant/chat with department head query."""
        response = self.app.post('/api/assistant/chat',
                                 data=json.dumps({"message": "Who is head of computer science?"}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['intent'], 'department_info')
        self.assertIn('Dr. Alan Vance', data['reply'])

    def test_assistant_chat_fallback(self):
        """Test POST /api/assistant/chat with unrecognizable text returns polite fallback."""
        response = self.app.post('/api/assistant/chat',
                                 data=json.dumps({"message": "xyzqwertyunknown 999"}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['intent'], 'fallback')
        self.assertGreaterEqual(len(data['suggestions']), 3)

    def test_assistant_chat_validation_empty(self):
        """Test POST /api/assistant/chat returns 400 for empty or whitespace message."""
        response = self.app.post('/api/assistant/chat',
                                 data=json.dumps({"message": "   "}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_assistant_chat_validation_invalid_json(self):
        """Test POST /api/assistant/chat returns 400 when invalid payload is sent."""
        response = self.app.post('/api/assistant/chat',
                                 data="not valid json",
                                 content_type='text/plain')
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
