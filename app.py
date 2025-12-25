# app.py
import os
import secrets
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
# Importamos 'or_' para consultas complejas de búsqueda
from sqlalchemy import or_

# Importaciones locales
from db import db
from users import User
from superusers import create_default_superusers
from workers import workers_bp

# Configuración inicial
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

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.config['UPLOAD_FOLDER'], picture_fn)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    form_picture.save(picture_path)
    return picture_fn

# --- RUTAS PRINCIPALES ---

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
                whatsapp=request.form.get('whatsapp')
            )
        else: # Empresa
            new_user = User(
                email=email, password=hashed_password, user_type='Empresa', role='regular',
                nombre_empresa=request.form.get('nombre_empresa'),
                encargado=request.form.get('encargado'),
                contacto=request.form.get('contacto'),
                telefono_fijo=request.form.get('telefono_fijo'),
                movil=request.form.get('movil'),
                whatsapp=request.form.get('whatsapp_empresa'),
                direccion=request.form.get('direccion'),
                otros_detalles=request.form.get('otros_detalles')
            )
            
        db.session.add(new_user)
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
    return render_template('perfil.html')

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
                    print(f"Error subiendo imagen: {e}")
                    flash(f'Error al subir imagen: {str(e)}', 'danger')

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
            print(f"Error DB: {e}")
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

# --- RUTA DASHBOARD CON BÚSQUEDA Y PAGINACIÓN ---
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role not in ['superuser', 'admin']:
        abort(403)
        
    # Parámetros de URL
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '', type=str)
    
    query = User.query

    # Lógica de Búsqueda
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
    
    # Paginación (10 items por página)
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    users = pagination.items
    
    total_users = User.query.count()
    total_workers = 0 
    
    return render_template('dashboard.html', 
                           users=users, 
                           pagination=pagination, 
                           search_query=search_query,
                           total_users=total_users, 
                           total_workers=total_workers)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- RUTAS ADMINISTRATIVAS ---

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
         flash('No puedes eliminar tu propia cuenta desde aquí.', 'warning')
         return redirect(url_for('dashboard'))

    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado exitosamente.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/update_role/<int:id>', methods=['POST'])
@login_required
def update_role(id):
    if current_user.role != 'superuser':
        flash('Acceso denegado. Solo superusuarios.', 'danger')
        return redirect(url_for('dashboard'))
        
    user = db.session.get(User, id)
    if not user:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('dashboard'))

    new_role = request.form.get('role')
    if new_role in ['regular', 'admin', 'superuser']:
        user.role = new_role
        db.session.commit()
        flash(f'Rol de {user.email} actualizado a {new_role}.', 'success')
    else:
        flash('Rol inválido.', 'danger')
        
    return redirect(url_for('dashboard'))

@app.route('/admin/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user_admin(id):
    if current_user.role != 'superuser':
        flash('Acceso denegado. Solo superusuarios.', 'danger')
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
            flash(f'Información de {user.email} actualizada.', 'success')
            return redirect(url_for('dashboard'))
        except:
            db.session.rollback()
            flash('Error al actualizar usuario.', 'danger')
            
    return render_template('admin_edit_user.html', user=user)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_superusers(app, bcrypt)
    app.run(debug=True)