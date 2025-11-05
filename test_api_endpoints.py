#!/usr/bin/env python3
"""
Script para testar endpoints da API do Super Admin
"""

import requests
import json

# Configurações
BASE_URL = "http://localhost:5000/api"
SUPER_ADMIN_EMAIL = "superadmin@federal.com"
SUPER_ADMIN_PASSWORD = "admin123"

def test_login():
    """Testa o login do Super Admin"""
    print("🔐 Testando login do Super Admin...")
    
    login_data = {
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Login bem-sucedido!")
            print(f"Token: {token[:50]}...")
            return token
        else:
            print(f"❌ Erro no login: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na requisição de login: {e}")
        return None

def test_users_endpoint(token):
    """Testa o endpoint /admin/users"""
    print("\n👥 Testando endpoint /admin/users...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Teste sem parâmetros
        response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            print(f"✅ Endpoint funcionando! Usuários encontrados: {len(users)}")
            for user in users[:3]:  # Mostrar apenas os primeiros 3
                print(f"  - {user.get('name')} ({user.get('email')}) - {user.get('user_type')}")
        else:
            print(f"❌ Erro: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_permissions_endpoint(token):
    """Testa o endpoint /admin/permissions"""
    print("\n🔐 Testando endpoint /admin/permissions...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/admin/permissions", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200:
            data = response.json()
            permissions = data.get("permissions", {})
            print(f"✅ Endpoint funcionando! Categorias de permissões: {len(permissions)}")
            for category, perms in permissions.items():
                print(f"  - {category}: {len(perms)} permissões")
        else:
            print(f"❌ Erro: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_health_endpoint():
    """Testa o endpoint de health check"""
    print("\n❤️ Testando endpoint /api/health...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check OK: {data}")
        else:
            print(f"❌ Erro: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def main():
    print("🧪 Testando APIs do Super Admin")
    print("=" * 50)
    
    # 1. Testar health check
    test_health_endpoint()
    
    # 2. Fazer login
    token = test_login()
    
    if not token:
        print("❌ Não foi possível obter token. Parando testes.")
        return
    
    # 3. Testar endpoints protegidos
    test_users_endpoint(token)
    test_permissions_endpoint(token)
    
    print("\n" + "=" * 50)
    print("🏁 Testes concluídos!")

if __name__ == "__main__":
    main()