# workers.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from db import db
# Importamos los modelos de colaboradores
from collaborator_models import Conductor, Vehiculo

# Blueprint para rutas relacionadas con colaboradores
workers_bp = Blueprint('workers', __name__)

@workers_bp.route('/workers')
@login_required
def list_workers():
    # Validación de seguridad básica
    if current_user.role not in ['superuser', 'admin']:
        flash('Acceso Denegado', 'danger')
        return redirect(url_for('home'))
    
    conductores = Conductor.query.all()
    # Si aún no tienes una vista de lista específica, puedes redirigir o renderizar un placeholder
    # Por ahora, para evitar errores si falta el template, renderizamos el dashboard o un template simple
    return render_template('dashboard.html') 

@workers_bp.route('/workers/add', methods=['GET', 'POST'])
@login_required
def add_worker():
    # Solo administradores y superusuarios pueden agregar
    if current_user.role not in ['superuser', 'admin']:
        flash('Solo administradores pueden agregar colaboradores.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        try:
            # 1. Crear el objeto Conductor
            # NOTA: Se eliminaron categoria_letra y categoria_numero
            nuevo_conductor = Conductor(
                nombre=request.form.get('nombre'),
                cedula=request.form.get('cedula'),
                licencia_tipo=request.form.get('licencia_tipo'),
                telefono_fijo=request.form.get('telefono_fijo'),
                movil=request.form.get('movil'),
                email=request.form.get('email'),
                cantidad_unidades=int(request.form.get('cantidad_unidades', 0))
            )
            
            db.session.add(nuevo_conductor)
            db.session.flush() # Genera el ID del conductor antes de hacer commit final

            # 2. Crear los Vehículos asociados
            cantidad = int(request.form.get('cantidad_unidades', 0))
            
            # Flask recupera listas de valores para campos con el mismo nombre (name="marca[]")
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

            # Iterar y guardar cada vehículo
            for i in range(cantidad):
                # Validación simple para evitar errores de índice
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
                        # Solo guardamos el detalle si el select dice "Si"
                        detalle_gravamen=detalles_gravamen[i] if gravamenes_list[i] == 'Si' else None
                    )
                    db.session.add(nuevo_vehiculo)

            db.session.commit()
            flash('Conductor y unidades agregados exitosamente.', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            print(f"Error al guardar conductor: {e}")
            flash(f'Hubo un error al guardar los datos: {str(e)}', 'danger')

    return render_template('add_collaborator.html')