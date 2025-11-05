import sqlite3
import os

print("Verificando bancos de dados...")

# Verificar pasta instance
instance_path = 'instance'
if os.path.exists(instance_path):
    print(f"Pasta instance existe: {instance_path}")
    files = os.listdir(instance_path)
    print("Arquivos na pasta instance:")
    for file in files:
        print(f"  - {file}")
        
    # Verificar o banco federal_associados.db
    db_path = os.path.join(instance_path, 'federal_associados.db')
    if os.path.exists(db_path):
        print(f"\nConectando ao banco: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Listar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Tabelas encontradas:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Verificar usuários
        cursor.execute("SELECT email, user_type FROM users WHERE email = 'superadmin@federal.com'")
        result = cursor.fetchone()
        if result:
            print(f"\nSuper Admin encontrado:")
            print(f"  Email: {result[0]}")
            print(f"  Tipo: {result[1]}")
        else:
            print("\nSuper Admin NÃO encontrado!")
        
        conn.close()
    else:
        print(f"Banco não encontrado: {db_path}")
else:
    print("Pasta instance não existe!")

# Verificar outros bancos
print("\nOutros arquivos .db no diretório atual:")
for file in os.listdir('.'):
    if file.endswith('.db'):
        print(f"  - {file}")
        # Testar cada banco
        try:
            conn = sqlite3.connect(file)
            cursor = conn.cursor()
            cursor.execute("SELECT email, user_type FROM users WHERE email = 'superadmin@federal.com'")
            result = cursor.fetchone()
            if result:
                print(f"    ✅ Super Admin encontrado em {file}: {result[0]} ({result[1]})")
            conn.close()
        except:
            print(f"    ❌ Erro ao acessar {file}")