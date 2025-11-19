import requests
from io import BytesIO
import pandas as pd


API_BASE = "http://localhost:5000/api"
LOGIN_URL = f"{API_BASE}/auth/login"
UPLOAD_DDDS_URL = f"{API_BASE}/upload-ddds"
DDDS_URL = f"{API_BASE}/ddds"
DDDS_MANUAL_URL = f"{API_BASE}/ddds/manual"
DDDS_PREVIEW_URL = f"{API_BASE}/ddds/preview"
DDDS_STATS_URL = f"{API_BASE}/ddds/estatisticas"


def login(session: requests.Session, email: str, password: str) -> str:
    resp = session.post(LOGIN_URL, json={"email": email, "password": password})
    if resp.status_code != 200:
        raise RuntimeError(f"Falha no login ({resp.status_code}): {resp.text}")
    data = resp.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        raise RuntimeError("Login retornou resposta sem token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    return token


def build_test_excel() -> BytesIO:
    # Monta um Excel válido para o endpoint de upload
    df = pd.DataFrame([
        {
            "DDD": "12",
            "Operadora": "OperadoraX",
            "Tipo Chip": "vazia",
            "Especificação": "150GB",
            "linha": "12ABCD",
        },
        {
            "DDD": "13",
            "Operadora": "OperadoraY",
            "Tipo Chip": "smp",
            "Especificação": "150GB",
            "linha": "13EFGH",
        },
    ])

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output


def main():
    session = requests.Session()
    report = {
        "login": None,
        "preview_manual": None,
        "add_manual": None,
        "list_after_manual": None,
        "stats_after_manual": None,
        "duplicate_manual": None,
        "upload_excel": None,
        "list_after_upload": None,
        "arquivo_origem_check": None,
        "cleanup": None,
        "final_stats": None,
    }

    # Credenciais padrão de superadmin (conforme scripts existentes)
    email = "superadmin@federal.com"
    password = "admin123"

    try:
        # Login
        token = login(session, email, password)
        report["login"] = {"status": "ok", "token_len": len(token)}

        # Preview manual
        manual_payload = {
            "ddd": "12",
            "operadora": "OperadoraX",
            "tipo_chip": "vazia",
            "especificacao": "150GB",
        }
        r_prev = session.post(DDDS_PREVIEW_URL, json=manual_payload)
        report["preview_manual"] = {"status_code": r_prev.status_code}
        r_prev.raise_for_status()
        prev_json = r_prev.json()
        assert prev_json.get("success") is True, "Preview não retornou success=True"
        assert prev_json["preview"]["source_name"] == "MANUAL", "Preview não está marcando como MANUAL"

        # Adição manual
        r_add = session.post(DDDS_MANUAL_URL, json=manual_payload)
        report["add_manual"] = {"status_code": r_add.status_code, "body": r_add.text[:200]}
        if r_add.status_code not in (200, 201):
            r_add.raise_for_status()
        add_json = r_add.json()
        ddd_added = add_json.get("ddd") or {}
        manual_id = ddd_added.get("id")
        assert ddd_added.get("arquivo_origem") == "MANUAL", "arquivo_origem do manual deve ser MANUAL"

        # Listagem (após manual)
        r_list = session.get(DDDS_URL, params={"per_page": 100})
        r_list.raise_for_status()
        list_json = r_list.json()
        found_manual = next((d for d in list_json.get("ddds", []) if d.get("id") == manual_id), None)
        report["list_after_manual"] = {"found_manual": bool(found_manual)}

        # Estatísticas (após manual)
        r_stats = session.get(DDDS_STATS_URL)
        r_stats.raise_for_status()
        stats_json = r_stats.json()
        report["stats_after_manual"] = {"total": stats_json.get("total")}

        # Duplicata manual (espera 409)
        r_dup = session.post(DDDS_MANUAL_URL, json=manual_payload)
        report["duplicate_manual"] = {"status_code": r_dup.status_code}
        assert r_dup.status_code == 409, "Cadastro duplicado manual deveria retornar 409"

        # Upload Excel
        excel_bytes = build_test_excel()
        files = {
            "file": (
                "test_upload_ddds.xlsx",
                excel_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        r_upload = session.post(UPLOAD_DDDS_URL, files=files)
        report["upload_excel"] = {"status_code": r_upload.status_code, "body": r_upload.text[:200]}
        r_upload.raise_for_status()
        upload_json = r_upload.json()
        assert upload_json.get("success") is True, "Upload não retornou success=True"

        # Listar novamente e validar arquivo_origem do registro 13
        r_list2 = session.get(DDDS_URL, params={"per_page": 200})
        r_list2.raise_for_status()
        list2_json = r_list2.json()
        ddd_13 = next(
            (d for d in list2_json.get("ddds", []) if d.get("ddd") == "13" and d.get("operadora") == "OperadoraY"),
            None,
        )
        assert ddd_13 is not None, "DDD 13 inserido via upload não encontrado"
        report["list_after_upload"] = {"found_13": True}
        report["arquivo_origem_check"] = {
            "ddd_13_arquivo_origem": ddd_13.get("arquivo_origem"),
            "ok": ddd_13.get("arquivo_origem") == "test_upload_ddds.xlsx",
        }

        # Cleanup: remover registros criados (manual + 13 do upload)
        cleanup_ok = True
        # Remover manual
        if manual_id:
            r_del_manual = session.delete(f"{DDDS_URL}/{manual_id}")
            cleanup_ok = cleanup_ok and (r_del_manual.status_code == 200)
        # Remover 13 (upload)
        ddd_13_id = ddd_13.get("id")
        if ddd_13_id:
            r_del_13 = session.delete(f"{DDDS_URL}/{ddd_13_id}")
            cleanup_ok = cleanup_ok and (r_del_13.status_code == 200)
        report["cleanup"] = {"ok": cleanup_ok}

        # Estatísticas finais
        r_stats2 = session.get(DDDS_STATS_URL)
        r_stats2.raise_for_status()
        report["final_stats"] = {"total": r_stats2.json().get("total")}

    except Exception as e:
        print("[ERRO]", str(e))
        raise
    finally:
        print("\n===== RELATÓRIO FINAL =====")
        for k, v in report.items():
            print(f"- {k}: {v}")


if __name__ == "__main__":
    main()