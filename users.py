# users.py
from db import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    
    # Campos generales de Login
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='regular') # regular, admin, superuser
    
    # Tipo de usuario (Persona, Empresa)
    user_type = db.Column(db.String(50)) 

    # Campos Persona
    avatar = db.Column(db.String(255), default='default.jpg')
    nombre = db.Column(db.String(100), nullable=True)
    primer_apellido = db.Column(db.String(100), nullable=True)
    segundo_apellido = db.Column(db.String(100), nullable=True)
    
    # Campos Empresa
    nombre_empresa = db.Column(db.String(150), nullable=True)
    encargado = db.Column(db.String(150), nullable=True)
    contacto = db.Column(db.String(150), nullable=True)
    telefono_fijo = db.Column(db.String(50), nullable=True)
    direccion = db.Column(db.Text, nullable=True)
    otros_detalles = db.Column(db.Text, nullable=True)

    # Campos Comunes de contacto
    telefono = db.Column(db.String(50), nullable=True)
    movil = db.Column(db.String(50), nullable=True)
    whatsapp = db.Column(db.String(50), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.email}>'