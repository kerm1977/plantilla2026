from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from sqlalchemy import or_, extract
import os
from werkzeug.utils import secure_filename

def init_routes(app, db, bcrypt):
    from messages_model import Message
    from users import User
    from notifications import Notification
    from collaborator_models import Conductor
    from superusers import create_default_superusers

    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        if current_user.role not in ['superuser', 'admin']:
            abort(403)
        
        # Lógica del dashboard
        total_users = User.query.count()
        total_workers = Conductor.query.count()
        
        # Obtener notificaciones recientes
        notifications = Notification.query.filter_by(user_id=current_user.id)\
            .order_by(Notification.created_at.desc())\
            .limit(5).all()
            
        return render_template('dashboard.html', 
                            total_users=total_users,
                            total_workers=total_workers,
                            notifications=notifications)

    # Aquí puedes agregar más rutas según sea necesario
    # Por ejemplo:
    # @app.route('/admin/message-history')
    # def admin_message_history():
    #     # Lógica para el historial de mensajes
    #     pass
