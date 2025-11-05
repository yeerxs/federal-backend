#!/usr/bin/env python3
"""
Script para testar como o backend trata o parâmetro user_type=undefined
"""

import requests
import json

# Configurações
BASE_URL = "http://localhost:5000/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
USERS_URL = f"{BASE_URL}/admin/users"

def test_user_type_undefined():
    print("🧪 Testando parâmetro user_type=undefined")
    
    # 1. Fazer login como Super Admin
    login_data = {
        "email": "superadmin@federal.com",
        "password": "admin123"
    }
    
    print("🔐 Fazendo login como Super Admin...")
    login_response = requests.post(LOGIN_URL, json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Erro no login: {login_response.status_code}")
        print(f"Resposta: {login_response.text}")
        return
    
    token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login realizado com sucesso!")
    
    # 2. Testar diferentes valores de user_type
    test_cases = [
        {"name": "Sem parâmetro user_type", "params": {}},
        {"name": "user_type=undefined", "params": {"user_type": "undefined"}},
        {"name": "user_type=all", "params": {"user_type": "all"}},
        {"name": "user_type=''", "params": {"user_type": ""}},
        {"name": "user_type=cliente", "params": {"user_type": "cliente"}},
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Testando: {test_case['name']}")
        print(f"   Parâmetros: {test_case['params']}")
        
        response = requests.get(USERS_URL, params=test_case['params'], headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            users_count = len(data.get('users', []))
            print(f"   ✅ Sucesso: {users_count} usuários retornados")
            
            if users_count > 0:
                print(f"   📋 Tipos de usuários encontrados:")
                user_types = set(user.get('user_type') for user in data.get('users', []))
                for user_type in sorted(user_types):
                    count = sum(1 for user in data.get('users', []) if user.get('user_type') == user_type)
                    print(f"      - {user_type}: {count}")
        else:
            print(f"   ❌ Erro: {response.status_code}")
            print(f"   Resposta: {response.text}")

if __name__ == "__main__":
    test_user_type_undefined()