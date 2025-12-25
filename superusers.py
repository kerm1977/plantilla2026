# superusers.py
from db import db
from users import User

def create_default_superusers(app, bcrypt):
    """
    Crea los superusuarios por defecto si no existen en la base de datos.
    """
    with app.app_context():
        # Lista de superusuarios a verificar/crear
        admins = [
            {"email": "lthikingcr@gmail.com", "pass": "CR129x7848n"},
            {"email": "kenth1977@gmail.com", "pass": "CR129x7848n"}
        ]

        for admin_data in admins:
            user = User.query.filter_by(email=admin_data["email"]).first()
            if not user:
                hashed_password = bcrypt.generate_password_hash(admin_data["pass"]).decode('utf-8')
                new_admin = User(
                    email=admin_data["email"],
                    password=hashed_password,
                    role='superuser',
                    user_type='Persona',
                    nombre='Super',
                    primer_apellido='Admin',
                    telefono='00000000'
                )
                db.session.add(new_admin)
                print(f"Superusuario creado: {admin_data['email']}")
            else:
                print(f"Superusuario ya existe: {admin_data['email']}")
        
        db.session.commit()