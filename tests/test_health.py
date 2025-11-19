import os
import sys

SRC_PATH = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.append(os.path.abspath(SRC_PATH))

from app import create_app


def test_health_endpoint():
    app = create_app()
    with app.test_client() as client:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get("status") == "ok"
