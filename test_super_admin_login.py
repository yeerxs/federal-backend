#!/usr/bin/env python3

import requests
import json

def test_super_admin_login():
    base_url = "http://localhost:5000"
    
    # Dados de login do super admin
    login_data = {
        "email": "superadmin@federal.com",
        "password": "admin123"
    }
    
    try:
        print("🔐 Testando login do Super Admin...")
        print(f"📧 Email: {login_data['email']}")
        
        # Fazer login
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        
        print(f"📊 Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login realizado com sucesso!")
            print(f"👤 Usuário: {data.get('user', {}).get('name')}")
            print(f"🏷️ Tipo: {data.get('user', {}).get('user_type')}")
            print(f"📧 Email: {data.get('user', {}).get('email')}")
            print(f"🔑 Token: {data.get('access_token', 'N/A')[:50]}...")
            
            # Testar acesso a uma rota protegida
            headers = {
                'Authorization': f"Bearer {data.get('access_token')}"
            }
            
            print("\n🔒 Testando acesso a rota protegida...")
            profile_response = requests.get(f"{base_url}/api/auth/profile", headers=headers)
            
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                print("✅ Acesso autorizado!")
                print(f"👤 Perfil: {profile_data}")
            else:
                print(f"❌ Erro ao acessar perfil: {profile_response.status_code}")
                print(f"📄 Resposta: {profile_response.text}")
                
        else:
            print(f"❌ Erro no login: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao backend")
        print("💡 Verifique se o backend está rodando em http://localhost:5000")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    test_super_admin_login()