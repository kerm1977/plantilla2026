# workers.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user

# Blueprint para rutas relacionadas con colaboradores (futuro)
workers_bp = Blueprint('workers', __name__)

@workers_bp.route('/workers')
@login_required
def list_workers():
    # Solo accesible para admin/superuser
    if current_user.role not in ['superuser', 'admin']:
        return "Acceso Denegado", 403
    return "Lista de Colaboradores (En construcción)"