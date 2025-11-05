import sys
sys.path.append('.')
from src.models.user import db, DDD, User
from src.app import create_app

app = create_app()
with app.app_context():
    admin_user = User.query.filter_by(user_type='admin').first()
    if admin_user:
        print(f'Admin encontrado: {admin_user.name}')
        
        # Criar DDDs de teste
        test_ddds = [
            {'operator': 'vivo', 'ddd': '11'},
            {'operator': 'claro', 'ddd': '11'},
            {'operator': 'tim', 'ddd': '11'},
            {'operator': 'vivo', 'ddd': '21'},
            {'operator': 'claro', 'ddd': '21'},
            {'operator': 'tim', 'ddd': '21'}
        ]
        
        created = 0
        for ddd_data in test_ddds:
            existing = DDD.query.filter_by(operator=ddd_data['operator'], ddd=ddd_data['ddd']).first()
            if not existing:
                new_ddd = DDD(operator=ddd_data['operator'], ddd=ddd_data['ddd'], is_active=True, created_by=admin_user.id)
                db.session.add(new_ddd)
                created += 1
                print(f'Criado DDD {ddd_data["ddd"]} para {ddd_data["operator"]}')
            else:
                print(f'DDD {ddd_data["ddd"]} para {ddd_data["operator"]} ja existe')
        
        db.session.commit()
        print(f'{created} DDDs criados com sucesso!')
    else:
        print('Nenhum admin encontrado')