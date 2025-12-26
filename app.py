# app.py
import os
import secrets
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_, extract

# Importaciones locales
from db import db
from users import User
from superusers import create_default_superusers
from workers import workers_bp
from notifications import Notification
from messages_model import Message
from collaborator_models import Conductor

# Configuración de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'img')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

app.register_blueprint(workers_bp)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- LÓGICA DE NOTIFICACIONES Y CUMPLEAÑOS ---

def check_birthdays_and_notify():
    """Genera notificaciones de cumpleaños. Se ejecuta antes de cada petición."""
    if not current_user.is_authenticated or current_user.role != 'superuser':
        return

    today = date.today()
    try:
        birthday_users = User.query.filter(
            extract('month', User.fecha_nacimiento) == today.month,
            extract('day', User.fecha_nacimiento) == today.day
        ).all()
    except Exception:
        all_users = User.query.all()
        birthday_users = [u for u in all_users if u.fecha_nacimiento and u.fecha_nacimiento.month == today.month and u.fecha_nacimiento.day == today.day]

    for b_user in birthday_users:
        nombre_cumple = b_user.nombre if b_user.user_type == 'Persona' else b_user.nombre_empresa
        mensaje = f"🎂 ¡Hoy es el cumpleaños de {nombre_cumple}!"
        
        # Evitar duplicados para el mismo día
        exists = Notification.query.filter_by(
            user_id=current_user.id,
            message=mensaje
        ).filter(extract('year', Notification.created_at) == today.year).first()

        if not exists:
            db.session.add(Notification(user_id=current_user.id, message=mensaje))
    
    try:
        db.session.commit()
    except:
        db.session.rollback()

@app.before_request
def before_request_func():
    """Mantenimiento y verificación antes de cualquier ruta."""
    if current_user.is_authenticated and not request.path.startswith('/static'):
        if current_user.role == 'superuser':
            check_birthdays_and_notify()

@app.context_processor
def inject_navbar_data():
    """Inyecta datos en el Navbar con nombres únicos para evitar conflictos con otras vistas.
    Ahora combina notificaciones y mensajes en la campana de notificaciones."""
    if current_user.is_authenticated:
        # Forzar refresco para ver cambios inmediatos
        db.session.expire_all()
        
        # Obtener notificaciones no leídas
        notifs = Notification.query.filter_by(
            user_id=current_user.id, 
            is_read=False
        ).order_by(Notification.created_at.desc()).all()
        
        # Obtener mensajes no leídos
        unread_msgs = Message.query.filter_by(
            recipient_id=current_user.id, 
            is_read=False
        ).order_by(Message.created_at.desc()).all()
        
        # Crear lista combinada de notificaciones y mensajes
        combined_notifs = []
        
        # Convertir mensajes a formato de notificación para mostrarlos juntos
        for msg in unread_msgs:
            # Usar un diccionario con la misma estructura que las notificaciones
            combined_notifs.append({
                'id': f'msg_{msg.id}',
                'message': f'📩 {msg.subject}: {msg.body[:50]}...',
                'created_at': msg.created_at,
                'is_message': True,
                'message_id': msg.id
            })
        
        # Agregar notificaciones normales
        for notif in notifs:
            combined_notifs.append({
                'id': f'notif_{notif.id}',
                'message': notif.message,
                'created_at': notif.created_at,
                'is_notification': True,
                'notification_id': notif.id
            })
        
        # Ordenar por fecha (más recientes primero)
        combined_notifs.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Limitar a las 10 más recientes para el dropdown
        notifs_list = combined_notifs[:10]
        
        # Contadores
        total_notifs = len(notifs)
        total_msgs = len(unread_msgs)
        total_combined = total_notifs + total_msgs
        
        return {
            'nav_notifs': notifs_list,
            'nav_notifs_count': total_combined,  # Total combinado para el contador
            'nav_messages_count': total_msgs,    # Solo mensajes para el buzón
            'has_notifications': total_combined > 0
        }
    return {}

def save_picture(form_picture):
    """Procesamiento de imagen de perfil."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.config['UPLOAD_FOLDER'], picture_fn)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    form_picture.save(picture_path)
    return picture_fn

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=remember)
            flash('Has iniciado sesión correctamente.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Error al iniciar sesión. Verifica email y contraseña.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated and current_user.role not in ['superuser', 'admin']:
        return redirect(url_for('home'))

    if request.method == 'POST':
        tipo = request.form.get('tipo_registro')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        fecha_nacimiento_str = request.form.get('fecha_nacimiento')
        
        fecha_nacimiento = None
        if fecha_nacimiento_str:
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado.', 'warning')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        if tipo == 'Persona':
            new_user = User(
                email=email, password=hashed_password, user_type='Persona', role='regular',
                nombre=request.form.get('nombre'),
                primer_apellido=request.form.get('primer_apellido'),
                segundo_apellido=request.form.get('segundo_apellido'),
                telefono=request.form.get('telefono'),
                whatsapp=request.form.get('whatsapp'),
                fecha_nacimiento=fecha_nacimiento
            )
        else: 
            new_user = User(
                email=email, password=hashed_password, user_type='Empresa', role='regular',
                nombre_empresa=request.form.get('nombre_empresa'),
                encargado=request.form.get('encargado'),
                contacto=request.form.get('contacto'),
                telefono_fijo=request.form.get('telefono_fijo'),
                movil=request.form.get('movil'),
                whatsapp=request.form.get('whatsapp_empresa'),
                direccion=request.form.get('direccion'),
                otros_detalles=request.form.get('otros_detalles'),
                fecha_nacimiento=fecha_nacimiento
            )
            
        db.session.add(new_user)
        db.session.flush() 
        
        # Notificar a administradores
        admins = User.query.filter(User.role.in_(['superuser', 'admin'])).all()
        identificador = new_user.nombre if new_user.user_type == 'Persona' else new_user.nombre_empresa
        mensaje = f"Nuevo registro: {identificador} ({new_user.user_type})"
        
        for admin_user in admins:
            notif = Notification(user_id=admin_user.id, message=mensaje)
            db.session.add(notif)

        db.session.commit()
        
        if current_user.is_authenticated and current_user.role in ['superuser', 'admin']:
            flash(f'Usuario {email} creado exitosamente.', 'success')
            return redirect(url_for('dashboard'))
            
        flash('Cuenta creada exitosamente. Por favor inicia sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/perfil')
@login_required
def perfil():
    messages = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.created_at.desc()).all()
    return render_template('perfil.html', messages=messages)

@app.route('/admin/broadcast', methods=['POST'])
@login_required
def broadcast_message():
    if current_user.role not in ['superuser', 'admin']:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('dashboard'))
        
    subject = request.form.get('subject')
    body = request.form.get('body')
    
    if not subject or not body:
        flash('El asunto y el mensaje son obligatorios.', 'warning')
        return redirect(url_for('dashboard'))
        
    try:
        users = User.query.all()
        count = 0
        for user in users:
            msg = Message(
                recipient_id=user.id,
                sender_id=current_user.id,
                subject=subject,
                body=body
            )
            db.session.add(msg)
            count += 1
            
        db.session.commit()
        flash(f'Mensaje enviado exitosamente a {count} usuarios.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al enviar el mensaje masivo.', 'danger')
        
    return redirect(url_for('dashboard'))

@app.route('/user/message/<int:id>/read', methods=['POST'])
@login_required
def read_message(id):
    msg = db.session.get(Message, id)
    if not msg or msg.recipient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    if not msg.is_read:
        msg.is_read = True
        db.session.commit()
    unread_count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    return jsonify({'status': 'success', 'unread_count': unread_count})

@app.route('/notifications/read', methods=['POST'])
@login_required
def mark_notifications_read():
    try:
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/editar_perfil', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    if request.method == 'POST':
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '':
                try:
                    picture_file = save_picture(file)
                    current_user.avatar = picture_file
                except Exception as e:
                    flash(f'Error al subir imagen: {str(e)}', 'danger')

        fecha_nacimiento_str = request.form.get('fecha_nacimiento')
        if fecha_nacimiento_str:
            try:
                current_user.fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        if current_user.user_type == 'Persona':
            current_user.nombre = request.form.get('nombre')
            current_user.primer_apellido = request.form.get('primer_apellido')
            current_user.segundo_apellido = request.form.get('segundo_apellido')
            current_user.telefono = request.form.get('telefono')
        else:
            current_user.nombre_empresa = request.form.get('nombre_empresa')
            current_user.encargado = request.form.get('encargado')
            current_user.contacto = request.form.get('contacto')
            current_user.telefono_fijo = request.form.get('telefono_fijo')
            current_user.movil = request.form.get('movil')
            current_user.direccion = request.form.get('direccion')
            current_user.otros_detalles = request.form.get('otros_detalles')
            
        current_user.whatsapp = request.form.get('whatsapp')
        
        try:
            db.session.commit()
            flash('Perfil actualizado correctamente.', 'success')
            return redirect(url_for('perfil'))
        except Exception as e:
            db.session.rollback()
            flash('Hubo un error al guardar.', 'danger')
        
    return render_template('editar_perfil.html')

@app.route('/cambiar_password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    if request.method == 'GET':
        return redirect(url_for('perfil'))
    current_pass = request.form.get('current_password')
    new_pass = request.form.get('new_password')
    confirm_pass = request.form.get('confirm_new_password')
    if not bcrypt.check_password_hash(current_user.password, current_pass):
        flash('La contraseña actual es incorrecta.', 'danger')
        return redirect(url_for('perfil'))
    elif new_pass != confirm_pass:
        flash('Las nuevas contraseñas no coinciden.', 'danger')
        return redirect(url_for('perfil'))
    else:
        current_user.password = bcrypt.generate_password_hash(new_pass).decode('utf-8')
        db.session.commit()
        flash('Contraseña actualizada correctamente.', 'success')
        return redirect(url_for('perfil'))

@app.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'GET':
        return redirect(url_for('perfil'))
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    flash('Tu cuenta ha sido eliminada.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role not in ['superuser', 'admin']:
        abort(403)
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '', type=str)
    query = User.query
    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(or_(
            User.nombre.ilike(search_filter),
            User.primer_apellido.ilike(search_filter),
            User.segundo_apellido.ilike(search_filter),
            User.nombre_empresa.ilike(search_filter),
            User.email.ilike(search_filter),
            User.role.ilike(search_filter),
            User.telefono.ilike(search_filter),
            User.telefono_fijo.ilike(search_filter),
            User.movil.ilike(search_filter)
        ))
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    users = pagination.items
    total_users = User.query.count()
    try:
        total_workers = Conductor.query.count()
    except:
        total_workers = 0 
    return render_template('dashboard.html', users=users, pagination=pagination, search_query=search_query, total_users=total_users, total_workers=total_workers)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/admin/delete_user/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_user_admin(id):
    if current_user.role != 'superuser':
        flash('Solo los Superusuarios pueden eliminar cuentas.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'GET':
        return redirect(url_for('dashboard'))
    user = db.session.get(User, id)
    if not user:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('dashboard'))
    if user.id == current_user.id:
         flash('No puedes eliminar tu propia cuenta.', 'warning')
         return redirect(url_for('dashboard'))
    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/update_role/<int:id>', methods=['POST'])
@login_required
def update_role(id):
    if current_user.role != 'superuser':
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('dashboard'))
    user = db.session.get(User, id)
    if not user:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('dashboard'))
    new_role = request.form.get('role')
    if new_role in ['regular', 'admin', 'superuser']:
        user.role = new_role
        db.session.commit()
        flash(f'Rol actualizado a {new_role}.', 'success')
    else:
        flash('Rol inválido.', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/admin/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user_admin(id):
    if current_user.role != 'superuser':
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('dashboard'))
    user = db.session.get(User, id)
    if not user:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if user.user_type == 'Persona':
            user.nombre = request.form.get('nombre')
            user.primer_apellido = request.form.get('primer_apellido')
            user.telefono = request.form.get('telefono')
        else:
            user.nombre_empresa = request.form.get('nombre_empresa')
            user.contacto = request.form.get('contacto')
        user.email = request.form.get('email')
        try:
            db.session.commit()
            flash('Usuario actualizado.', 'success')
            return redirect(url_for('dashboard'))
        except:
            db.session.rollback()
            flash('Error al actualizar.', 'danger')
    return render_template('admin_edit_user.html', user=user)

@app.route('/admin/report/data')
@login_required
def report_data():
    if current_user.role not in ['superuser', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    users = User.query.all()
    data = {'personas': [], 'empresas': []}
    for u in users:
        if u.user_type == 'Persona':
            nombre_completo = f"{u.nombre} {u.primer_apellido} {u.segundo_apellido or ''}".strip()
            data['personas'].append({'nombre': nombre_completo, 'email': u.email, 'telefono': u.telefono or 'N/A', 'role': u.role})
        else:
            data['empresas'].append({'nombre': u.nombre_empresa, 'contacto': u.contacto or 'N/A', 'email': u.email, 'telefono': u.telefono_fijo or u.movil or 'N/A', 'role': u.role})
    return jsonify(data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_superusers(app, bcrypt)
    app.run(debug=True)