# notifications.py
from db import db
from datetime import datetime

class Notification(db.Model):
    """
    Modelo para gestionar las notificaciones del sistema (ej. cumpleaños, nuevos registros).
    """
    __tablename__ = 'notifications'

    # Identificador único de la notificación
    id = db.Column(db.Integer, primary_key=True)
    
    # ID del usuario que debe recibir la alerta (normalmente un superusuario o admin)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Contenido del mensaje de la notificación
    message = db.Column(db.String(255), nullable=False)
    
    # Estado de lectura: False es nueva, True es leída
    is_read = db.Column(db.Boolean, default=False)
    
    # Fecha y hora de creación automática
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Notification {self.id} - User {self.user_id}>'