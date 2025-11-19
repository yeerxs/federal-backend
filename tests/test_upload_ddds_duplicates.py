from io import BytesIO
import pandas as pd
from flask_jwt_extended import create_access_token

from src.app import create_app


def make_excel_bytes_with_duplicates():
    df = pd.DataFrame([
        {"ddd": "32", "operadora": "Claro", "tipo_chip": "smp", "especificacao": "150GB"},
        {"ddd": "32", "operadora": "Claro", "tipo_chip": "smp", "especificacao": "150GB"},
    ])
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    bio.seek(0)
    return bio.read()


def test_upload_ddds_skips_batch_duplicates():
    app = create_app()
    with app.test_client() as client:
        with app.app_context():
            token = create_access_token(identity="test-user")

        excel_bytes = make_excel_bytes_with_duplicates()
        data = {"file": (BytesIO(excel_bytes), "dups.xlsx")}

        resp = client.post(
            "/api/upload-ddds",
            data=data,
            content_type="multipart/form-data",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200, resp.get_data(as_text=True)
        payload = resp.get_json()
        assert payload["success"] is True
        stats = payload.get("estatisticas", {})
        assert stats.get("novos_registros") == 1
        assert stats.get("duplicatas_encontradas") >= 1

