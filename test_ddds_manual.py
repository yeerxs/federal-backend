#!/usr/bin/env python3
"""
Script de testes para gerenciamento manual de DDDs:
- Tenta login com diferentes credenciais conhecidas
- Faz preview de DDD manual
- Adiciona DDD manualmente
- Lista DDDs para confirmar inclusão
- Remove o DDD adicionado
- Consulta estatísticas

O script adiciona e em seguida remove o DDD para não deixar dados de teste.
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def try_login():
    credenciais = [
        {"email": "superadmin@federal.com", "password": "admin123"},
        {"email": "admin@federal.com", "password": "admin123"},
        {"email": "admin@admin.com", "password": "admin123"},
        {"email": "superadmin@federal.com", "password": "superadmin"},
    ]

    for cred in credenciais:
        print(f"🔐 Tentando login com: {cred['email']}")
        try:
            resp = requests.post(f"{BASE_URL}/api/auth/login", json=cred)
        except requests.exceptions.ConnectionError:
            print("❌ Não foi possível conectar ao backend. Verifique se está rodando em http://localhost:5000")
            return None

        if resp.status_code == 200:
            data = resp.json()
            token = data.get("access_token")
            print("✅ Login bem-sucedido! Token obtido.")
            return token
        else:
            print(f"❌ Falha: {resp.status_code} - {resp.text}")

    return None

def preview_ddd(token, ddd_data):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("\n🔎 Fazendo preview do DDD...")
    resp = requests.post(f"{BASE_URL}/api/ddds/preview", headers=headers, json=ddd_data)
    print(f"Status: {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(resp.text[:200])
    return resp

def add_ddd(token, ddd_data):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("\n➕ Adicionando DDD manualmente...")
    resp = requests.post(f"{BASE_URL}/api/ddds/manual", headers=headers, json=ddd_data)
    print(f"Status: {resp.status_code}")
    try:
        data = resp.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print(resp.text[:200])
        data = None
    return resp, (data or {}).get("ddd", {}).get("id")

def list_ddds(token, page=1, per_page=10):
    headers = {"Authorization": f"Bearer {token}"}
    print("\n📋 Listando DDDs...")
    resp = requests.get(f"{BASE_URL}/api/ddds?page={page}&per_page={per_page}", headers=headers)
    print(f"Status: {resp.status_code}")
    try:
        data = resp.json()
        print(json.dumps({"pagination": data.get("pagination"), "first_items": data.get("ddds", [])[:3]}, indent=2, ensure_ascii=False))
    except Exception:
        print(resp.text[:200])
    return resp

def delete_ddd(token, ddd_id):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("\n🗑️  Removendo DDD adicionado...")
    resp = requests.delete(f"{BASE_URL}/api/ddds/{ddd_id}", headers=headers)
    print(f"Status: {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(resp.text[:200])
    return resp

def stats(token):
    headers = {"Authorization": f"Bearer {token}"}
    print("\n📊 Consultando estatísticas...")
    resp = requests.get(f"{BASE_URL}/api/ddds/estatisticas", headers=headers)
    print(f"Status: {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(resp.text[:200])
    return resp

def main():
    print("=== Testes de DDD Manual ===")
    token = try_login()
    if not token:
        print("❌ Não foi possível obter token. Abortando testes.")
        return

    # Dados válidos conforme validação existente (tipo_chip: vazia|smp, especificacao: 150GB)
    ddd_data = {
        "ddd": "11",
        "operadora": "VIVO",
        "tipo_chip": "vazia",
        "especificacao": "150GB"
    }

    # Preview
    preview_resp = preview_ddd(token, ddd_data)
    if preview_resp.status_code != 200:
        print("❌ Preview falhou. Abortando.")
        return

    # Adicionar
    add_resp, new_id = add_ddd(token, ddd_data)
    if add_resp.status_code not in (200, 201):
        print("❌ Falha ao adicionar DDD. Abortando.")
        return

    # Listar
    list_ddds(token)

    # Estatísticas
    stats(token)

    # Remover (limpeza)
    if new_id:
        delete_ddd(token, new_id)
    else:
        print("⚠️ Não foi possível obter ID do DDD adicionado para remoção.")

    print("\n✅ Testes concluídos.")

if __name__ == "__main__":
    main()