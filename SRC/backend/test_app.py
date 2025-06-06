import unittest
from app import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_alert_post(self):
        response = self.client.post('/alert', json={
            "lat": -12.0464,
            "lng": -77.0428,
            "hora": "17:40",
            "fecha": "08/05/2025"
        })
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()