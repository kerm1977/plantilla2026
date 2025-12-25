# superusers.py
import os
from db import db
from users import User

def create_default_superusers(app, bcrypt):
    """
    Crea los superusuarios por defecto si no existen en la base de datos.
    Se utiliza os.environ para no exponer la contraseña en el código.
    """
    with app.app_context():
        # Recuperamos la contraseña de las variables de entorno del sistema
        # Para que esto funcione, debes configurar la variable 'SUPERUSER_PASSWORD' en tu sistema
        # Ejemplo (Terminal): export SUPERUSER_PASSWORD='CR129x7848n'
        admin_password = os.environ.get('SUPERUSER_PASSWORD')

        if not admin_password:
            # Si no hay variable de entorno, evitamos crear usuarios con password vacío por seguridad
            # O podrías poner un fallback temporal solo para desarrollo: 'CR129x7848n'
            return

        admins = [
            {"email": "lthikingcr@gmail.com", "pass": admin_password},
            {"email": "kenth1977@gmail.com", "pass": admin_password}
        ]

        for admin_data in admins:
            user = User.query.filter_by(email=admin_data["email"]).first()
            if not user:
                # Utilizamos bcrypt para encriptar la contraseña obtenida
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
                # Silencioso: No imprimir confirmación en consola por seguridad
            else:
                # Silencioso: No revelar existencia de usuario en consola
                pass
        
        db.session.commit()