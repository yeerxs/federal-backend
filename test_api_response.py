#!/usr/bin/env python3
import requests
import json

def test_login_api():
    """Testa a API de login para verificar a estrutura da resposta"""
    
    url = "http://localhost:5000/api/auth/login"
    
    # Dados de login do Super Admin
    login_data = {
        "email": "superadmin@federal.com",
        "password": "admin123"
    }
    
    try:
        print("🔐 Testando API de login...")
        print(f"📧 URL: {url}")
        print(f"📊 Dados: {login_data}")
        
        response = requests.post(url, json=login_data)
        
        print(f"📊 Status: {response.status_code}")
        print(f"📄 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Resposta JSON:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Verificar se tem access_token
            if 'access_token' in data:
                print("✅ Campo 'access_token' encontrado!")
            else:
                print("❌ Campo 'access_token' NÃO encontrado!")
                print("🔍 Campos disponíveis:", list(data.keys()))
                
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    test_login_api()