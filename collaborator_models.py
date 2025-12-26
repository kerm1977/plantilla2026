# collaborator_models.py
from db import db
from datetime import datetime

class Conductor(db.Model):
    __tablename__ = 'conductores'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    cedula = db.Column(db.String(50), unique=True, nullable=False)
    licencia_tipo = db.Column(db.String(50))
    # Se eliminaron categoria_letra y categoria_numero
    telefono_fijo = db.Column(db.String(20))
    movil = db.Column(db.String(20))
    email = db.Column(db.String(150))
    cantidad_unidades = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación con vehículos
    vehiculos = db.relationship('Vehiculo', backref='conductor', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Conductor {self.nombre}>'

class Vehiculo(db.Model):
    __tablename__ = 'vehiculos'

    id = db.Column(db.Integer, primary_key=True)
    conductor_id = db.Column(db.Integer, db.ForeignKey('conductores.id'), nullable=False)
    
    marca = db.Column(db.String(100))
    anio = db.Column(db.Integer)
    capacidad = db.Column(db.Integer)
    placa = db.Column(db.String(20))
    tipo_servicio = db.Column(db.String(100)) # Estudiantes, Especiales
    color = db.Column(db.String(50))
    
    # Datos adicionales
    tiene_poliza = db.Column(db.String(10)) 
    al_dia = db.Column(db.String(10))
    tiene_gravamenes = db.Column(db.String(10))
    detalle_gravamen = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Vehiculo {self.placa}>'