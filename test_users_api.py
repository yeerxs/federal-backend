#!/usr/bin/env python3
"""
Script para testar a API de usuários diretamente
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def test_users_api():
    """Testar a API de usuários"""
    
    base_url = "http://localhost:5000/api"
    
    print("🔍 Testando API de usuários...")
    print("=" * 50)
    
    # 1. Fazer login como admin para obter token
    print("1. Fazendo login como admin...")
    
    login_data = {
        "email": "admin@federal.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"❌ Erro no login: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
        
        login_result = response.json()
        token = login_result.get('access_token')
        
        if not token:
            print("❌ Token não encontrado na resposta do login")
            return False
        
        print("✅ Login realizado com sucesso!")
        
        # 2. Testar endpoint de usuários
        print("\n2. Testando endpoint /admin/users...")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Teste sem filtros
        response = requests.get(f"{base_url}/admin/users", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Erro na API de usuários: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
        
        users_data = response.json()
        print("✅ API de usuários funcionando!")
        
        # 3. Analisar resposta
        print("\n3. Analisando resposta da API...")
        print(f"📊 Estrutura da resposta: {list(users_data.keys())}")
        
        users = users_data.get('users', [])
        pagination = users_data.get('pagination', {})
        
        print(f"📊 Usuários retornados: {len(users)}")
        print(f"📊 Paginação: {pagination}")
        
        if users:
            print("\n👥 Usuários encontrados:")
            for i, user in enumerate(users, 1):
                print(f"  {i}. {user.get('name')} ({user.get('email')}) - Tipo: {user.get('user_type')}")
        else:
            print("⚠️  Nenhum usuário retornado pela API!")
        
        # 4. Testar com diferentes filtros
        print("\n4. Testando filtros...")
        
        # Teste com filtro de tipo 'cliente'
        response = requests.get(f"{base_url}/admin/users?user_type=cliente", headers=headers)
        if response.status_code == 200:
            cliente_data = response.json()
            cliente_users = cliente_data.get('users', [])
            print(f"📊 Usuários tipo 'cliente': {len(cliente_users)}")
        
        # Teste com filtro de tipo 'admin'
        response = requests.get(f"{base_url}/admin/users?user_type=admin", headers=headers)
        if response.status_code == 200:
            admin_data = response.json()
            admin_users = admin_data.get('users', [])
            print(f"📊 Usuários tipo 'admin': {len(admin_users)}")
        
        # Teste com filtro de tipo 'operador' (que não deveria existir mais)
        response = requests.get(f"{base_url}/admin/users?user_type=operador", headers=headers)
        if response.status_code == 200:
            operador_data = response.json()
            operador_users = operador_data.get('users', [])
            print(f"📊 Usuários tipo 'operador': {len(operador_users)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar API: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Testando API de usuários...")
    print("=" * 50)
    
    success = test_users_api()
    
    print("=" * 50)
    if success:
        print("✅ Teste concluído!")
    else:
        print("❌ Teste falhou!")
        sys.exit(1)