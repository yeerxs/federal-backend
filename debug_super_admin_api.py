#!/usr/bin/env python3
"""
Script para debugar a API /admin/users com Super Admin
"""

import requests
import json
import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_super_admin_api():
    """Testa a API /admin/users com Super Admin"""
    
    base_url = "http://localhost:5000"
    
    print("🔐 Fazendo login como Super Admin...")
    
    # 1. Login
    login_data = {
        "email": "superadmin@federal.com",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"Status do login: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ Erro no login: {login_response.text}")
            return False
        
        login_result = login_response.json()
        token = login_result.get("access_token")
        user_info = login_result.get("user", {})
        
        print(f"✅ Login bem-sucedido!")
        print(f"👤 Usuário: {user_info.get('name')} ({user_info.get('email')})")
        print(f"🏷️ Tipo: {user_info.get('user_type')}")
        print(f"🔑 Token: {token[:50]}...")
        
        # 2. Testar API /admin/users
        print(f"\n📋 Testando API /admin/users...")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Testar sem filtros
        users_response = requests.get(f"{base_url}/api/admin/users", headers=headers)
        print(f"Status da API users: {users_response.status_code}")
        
        if users_response.status_code != 200:
            print(f"❌ Erro na API users: {users_response.text}")
            return False
        
        users_result = users_response.json()
        print(f"✅ API users funcionando!")
        print(f"📊 Resposta: {json.dumps(users_result, indent=2, ensure_ascii=False)}")
        
        # 3. Testar com diferentes filtros
        print(f"\n🔍 Testando com filtro user_type=cliente...")
        
        params = {"user_type": "cliente"}
        filtered_response = requests.get(f"{base_url}/api/admin/users", headers=headers, params=params)
        print(f"Status com filtro cliente: {filtered_response.status_code}")
        
        if filtered_response.status_code == 200:
            filtered_result = filtered_response.json()
            print(f"📊 Clientes encontrados: {len(filtered_result.get('users', []))}")
        
        # 4. Testar com filtro admin
        print(f"\n🔍 Testando com filtro user_type=admin...")
        
        params = {"user_type": "admin"}
        admin_response = requests.get(f"{base_url}/api/admin/users", headers=headers, params=params)
        print(f"Status com filtro admin: {admin_response.status_code}")
        
        if admin_response.status_code == 200:
            admin_result = admin_response.json()
            print(f"📊 Admins encontrados: {len(admin_result.get('users', []))}")
        
        # 5. Testar com filtro super_admin
        print(f"\n🔍 Testando com filtro user_type=super_admin...")
        
        params = {"user_type": "super_admin"}
        super_admin_response = requests.get(f"{base_url}/api/admin/users", headers=headers, params=params)
        print(f"Status com filtro super_admin: {super_admin_response.status_code}")
        
        if super_admin_response.status_code == 200:
            super_admin_result = super_admin_response.json()
            print(f"📊 Super Admins encontrados: {len(super_admin_result.get('users', []))}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor. Verifique se o backend está rodando.")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testando API /admin/users com Super Admin...")
    print("=" * 60)
    
    success = test_super_admin_api()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Teste concluído!")
    else:
        print("❌ Teste falhou!")