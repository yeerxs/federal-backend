from io import BytesIO
import pandas as pd
from flask_jwt_extended import create_access_token

import os, sys
SRC_PATH = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.append(os.path.abspath(SRC_PATH))
from app import create_app


def make_excel_bytes():
    df = pd.DataFrame([
        {
            "ddd": "11",
            "operadora": "VIVO",
            "tipo_chip": "vazia",
            "especificacao": "150GB",
        }
    ])
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    bio.seek(0)
    return bio.read()


def test_upload_ddds_success():
    app = create_app()
    with app.test_client() as client:
        with app.app_context():
            token = create_access_token(identity="test-user")

        excel_bytes = make_excel_bytes()
        data = {
            "file": (BytesIO(excel_bytes), "sample.xlsx"),
        }

        resp = client.post(
            "/api/upload-ddds",
            data=data,
            content_type="multipart/form-data",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200, resp.get_data(as_text=True)
        body = resp.get_json()
        assert body.get("success") is True
        stats = body.get("estatisticas", {})
        assert stats.get("novos_registros") == 1
