"""HTTP smoke checks for the actual chart routes and access guard."""
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from fusion.data import Store
from fusion.server import make_handler


class ChartsHttpSmokeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        store = Store(Path(self.tmp.name) / "test.sqlite")
        store.import_draws([
            {"issue": "2026001", "date": "2026-01-01", "numbers": list(range(1, 21))},
            {"issue": "2026002", "date": "2026-01-02", "numbers": list(range(21, 41))},
        ], "test")
        self.server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            make_handler(store, access_username="testuser",
                         access_password="testpasswordabcdefghijkl"))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:" + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.tmp.cleanup()

    def get(self, path, auth=True):
        headers = {}
        if auth:
            import base64
            token = base64.b64encode(b"testuser:testpasswordabcdefghijkl").decode("ascii")
            headers["Authorization"] = "Basic " + token
        return urlopen(Request(self.base + path, headers=headers), timeout=5)

    def test_authorization_and_health(self):
        with self.get("/api/health", auth=False) as response:
            self.assertEqual(response.status, 200)
        with self.assertRaises(HTTPError) as cm:
            self.get("/api/chart-series?limit=30", auth=False)
        self.assertEqual(cm.exception.code, 401)

    def test_charts_endpoint(self):
        with self.get("/api/chart-series?limit=30") as response:
            data = json.load(response)
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["rows"][-1]["positions"]), 20)
        self.assertIn("even_rotation", data["nineSquareLayouts"])
        self.assertIn("special", data["rows"][-1])

    def test_ranked_endpoint_and_invalid_input(self):
        with self.get("/api/ranked-series?mode=frequency&groups=4&lookback=1&limit=30") as response:
            data = json.load(response)
        self.assertIsNone(data["rows"][0]["counts"])
        self.assertEqual(sum(data["rows"][1]["counts"]), 20)
        with self.assertRaises(HTTPError) as cm:
            self.get("/api/ranked-series?mode=frequency&groups=3&limit=30")
        self.assertEqual(cm.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
