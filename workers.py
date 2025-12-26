# workers.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from db import db
from collaborator_models import Conductor, Vehiculo
from datetime import datetime

workers_bp = Blueprint('workers', __name__)

def calcular_edad(fecha_nacimiento):
    """Calcula la edad a partir de un objeto date o string YYYY-MM-DD."""
    if not fecha_nacimiento:
        return None
    if isinstance(fecha_nacimiento, str):
        try:
            fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
        except ValueError:
            return None
    hoy = datetime.now()
    return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

@workers_bp.route('/workers')
@login_required
def list_workers():
    if current_user.role not in ['superuser', 'admin']:
        flash('Acceso Denegado', 'danger')
        return redirect(url_for('home'))
    
    conductores = Conductor.query.all()
    # Añadimos la edad calculada dinámicamente para cada conductor en la lista
    for c in conductores:
        c.edad_actual = calcular_edad(c.fecha_nacimiento)
        
    return render_template('manage_workers.html', conductores=conductores)

@workers_bp.route('/workers/add', methods=['GET', 'POST'])
@login_required
def add_worker():
    if current_user.role not in ['superuser', 'admin']:
        flash('Solo administradores pueden agregar colaboradores.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        try:
            nuevo_conductor = Conductor(
                nombre=request.form.get('nombre'),
                cedula=request.form.get('cedula'),
                licencia_tipo=request.form.get('licencia_tipo'),
                telefono_fijo=request.form.get('telefono_fijo'),
                movil=request.form.get('movil'),
                email=request.form.get('email'),
                fecha_nacimiento=request.form.get('fecha_nacimiento'), # Nuevo campo
                foto=request.form.get('foto'), # Nuevo campo (URL o Base64)
                cantidad_unidades=int(request.form.get('cantidad_unidades', 0))
            )
            
            db.session.add(nuevo_conductor)
            db.session.flush()

            cantidad = int(request.form.get('cantidad_unidades', 0))
            marcas = request.form.getlist('marca[]')
            anios = request.form.getlist('anio[]')
            capacidades = request.form.getlist('capacidad[]')
            placas = request.form.getlist('placa[]')
            servicios = request.form.getlist('tipo_servicio[]')
            colores = request.form.getlist('color[]')
            polizas = request.form.getlist('poliza[]')
            al_dias = request.form.getlist('al_dia[]')
            gravamenes_list = request.form.getlist('gravamenes[]')
            detalles_gravamen = request.form.getlist('detalle_gravamen[]')

            for i in range(cantidad):
                if i < len(marcas):
                    nuevo_vehiculo = Vehiculo(
                        conductor_id=nuevo_conductor.id,
                        marca=marcas[i],
                        anio=anios[i],
                        capacidad=capacidades[i],
                        placa=placas[i],
                        tipo_servicio=servicios[i],
                        color=colores[i],
                        tiene_poliza=polizas[i],
                        al_dia=al_dias[i],
                        tiene_gravamenes=gravamenes_list[i],
                        detalle_gravamen=detalles_gravamen[i] if gravamenes_list[i] == 'Si' else None
                    )
                    db.session.add(nuevo_vehiculo)

            db.session.commit()
            flash('Conductor registrado exitosamente.', 'success')
            return redirect(url_for('workers.list_workers'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {str(e)}', 'danger')

    return render_template('add_collaborator.html')

@workers_bp.route('/workers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_worker(id):
    if current_user.role not in ['superuser', 'admin']:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('dashboard'))

    conductor = db.session.get(Conductor, id)
    if not conductor:
        flash('Colaborador no encontrado.', 'danger')
        return redirect(url_for('workers.list_workers'))

    if request.method == 'POST':
        try:
            conductor.nombre = request.form.get('nombre')
            conductor.cedula = request.form.get('cedula')
            conductor.licencia_tipo = request.form.get('licencia_tipo')
            conductor.telefono_fijo = request.form.get('telefono_fijo')
            conductor.movil = request.form.get('movil')
            conductor.email = request.form.get('email')
            conductor.fecha_nacimiento = request.form.get('fecha_nacimiento') # Actualizar
            conductor.foto = request.form.get('foto') # Actualizar
            
            nueva_cantidad = int(request.form.get('cantidad_unidades', 0))
            conductor.cantidad_unidades = nueva_cantidad

            Vehiculo.query.filter_by(conductor_id=conductor.id).delete()
            
            marcas = request.form.getlist('marca[]')
            anios = request.form.getlist('anio[]')
            capacidades = request.form.getlist('capacidad[]')
            placas = request.form.getlist('placa[]')
            servicios = request.form.getlist('tipo_servicio[]')
            colores = request.form.getlist('color[]')
            polizas = request.form.getlist('poliza[]')
            al_dias = request.form.getlist('al_dia[]')
            gravamenes_list = request.form.getlist('gravamenes[]')
            detalles_gravamen = request.form.getlist('detalle_gravamen[]')

            for i in range(nueva_cantidad):
                if i < len(marcas):
                    nuevo_vehiculo = Vehiculo(
                        conductor_id=conductor.id,
                        marca=marcas[i],
                        anio=anios[i],
                        capacidad=capacidades[i],
                        placa=placas[i],
                        tipo_servicio=servicios[i],
                        color=colores[i],
                        tiene_poliza=polizas[i],
                        al_dia=al_dias[i],
                        tiene_gravamenes=gravamenes_list[i],
                        detalle_gravamen=detalles_gravamen[i] if gravamenes_list[i] == 'Si' else None
                    )
                    db.session.add(nuevo_vehiculo)

            db.session.commit()
            flash('Información actualizada correctamente.', 'success')
            return redirect(url_for('workers.list_workers'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')

    return render_template('edit_collaborator.html', conductor=conductor)

@workers_bp.route('/workers/delete/<int:id>', methods=['POST'])
@login_required
def delete_worker(id):
    if current_user.role not in ['superuser', 'admin']:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('dashboard'))

    try:
        conductor = db.session.get(Conductor, id)
        if conductor:
            db.session.delete(conductor)
            db.session.commit()
            flash('Colaborador eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'danger')

    return redirect(url_for('workers.list_workers'))