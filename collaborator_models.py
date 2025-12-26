# collaborator_models.py
from db import db
from datetime import datetime

class Conductor(db.Model):
    """
    Modelo que representa a un conductor/colaborador en el sistema.
    """
    __tablename__ = 'conductores'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    licencia_tipo = db.Column(db.String(10))
    telefono_fijo = db.Column(db.String(20))
    movil = db.Column(db.String(20))
    email = db.Column(db.String(100))
    
    # Nuevos campos solicitados
    fecha_nacimiento = db.Column(db.String(10))  # Almacenado como YYYY-MM-DD
    foto = db.Column(db.Text)                    # Almacenado como Base64 o URL
    
    cantidad_unidades = db.Column(db.Integer, default=0)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación con vehículos
    vehiculos = db.relationship('Vehiculo', backref='conductor', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Conductor {self.nombre}>'

class Vehiculo(db.Model):
    """
    Modelo que representa las unidades/vehículos asociados a un conductor.
    """
    __tablename__ = 'vehiculos'

    id = db.Column(db.Integer, primary_key=True)
    conductor_id = db.Column(db.Integer, db.ForeignKey('conductores.id'), nullable=False)
    
    marca = db.Column(db.String(50))
    anio = db.Column(db.String(4))
    capacidad = db.Column(db.String(20))
    placa = db.Column(db.String(20), unique=True)
    tipo_servicio = db.Column(db.String(50))
    color = db.Column(db.String(30))
    
    tiene_poliza = db.Column(db.String(5))   # 'Si' o 'No'
    al_dia = db.Column(db.String(5))         # 'Si' o 'No'
    tiene_gravamenes = db.Column(db.String(5)) # 'Si' o 'No'
    detalle_gravamen = db.Column(db.Text)

    def __repr__(self):
        return f'<Vehiculo {self.placa}>'