from app import app

if __name__ == '__main__':
    print("🚀 Iniciando servidor Federal Associados...")
    print("📡 Servidor disponível em: http://localhost:5001")
    print("🔗 API disponível em: http://localhost:5001/api/")
    app.run(host='0.0.0.0', port=5001, debug=True)