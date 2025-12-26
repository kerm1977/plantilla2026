# superusers.py
import os
from db import db
from users import User

def create_default_superusers(app, bcrypt):
    """
    Crea los superusuarios por defecto si no existen en la base de datos.
    """
    with app.app_context():
        # Intentamos obtener la contraseña segura del sistema.
        # Si no existe (None), usamos la contraseña por defecto para desarrollo ('CR129x7848n')
        admin_password = os.environ.get('SUPERUSER_PASSWORD', 'CR129x7848n')

        if not admin_password:
            print("Error: No se pudo establecer una contraseña para superusuarios.")
            return

        admins = [
            {"email": "lthikingcr@gmail.com", "pass": admin_password},
            {"email": "kenth1977@gmail.com", "pass": admin_password}
        ]

        created_count = 0
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
                    telefono='00000000',
                    # Aseguramos compatibilidad con el nuevo campo fecha
                    fecha_nacimiento=None 
                )
                db.session.add(new_admin)
                created_count += 1
                # print(f"Superusuario creado: {admin_data['email']}") # Opcional: Descomentar para debug
        
        if created_count > 0:
            db.session.commit()
            print(f"Se han creado {created_count} superusuarios por defecto.")
        else:
            # print("Superusuarios ya existen.")
            pass