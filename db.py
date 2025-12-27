# db.py
from flask_sqlalchemy import SQLAlchemy

# Inicializamos la base de datos de forma independiente para evitar importaciones circulares
db = SQLAlchemy()