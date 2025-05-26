import os
import time
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
import requests
from werkzeug.utils import secure_filename
from flask_reuploads import UploadSet, configure_uploads, IMAGES

from models import FailedLoginAttempt, IdentificationChangeLog, UserProfile, UserRole, Voto, db, User
from config import Config
from forms import ChangePasswordForm, EditIdentificacionForm, EditProfileForm, EditarEleccionForm, LoginForm, RegisterForm
from flask import send_from_directory

from flask import send_file
from io import BytesIO

import os

from forms import CrearEleccionForm
from models import Eleccion
from sqlalchemy import desc
from datetime import datetime


from models import Candidatura
from forms import AgregarCandidaturaForm
from forms import VotarForm


app = Flask(__name__)
app.config.from_object(Config)

# Habilitar protección CSRF
csrf = CSRFProtect(app)
db.init_app(app)


# Configuración de subida de imágenes
app.config['UPLOADED_PHOTOS_DEST'] = 'uploads/photos'
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Debes iniciar sesión para acceder a esta página."
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/uploads/photos/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOADED_PHOTOS_DEST'], filename)

with app.app_context():
    db.create_all()

#------------------------------------------
#            ENDPOINT BASE
#------------------------------------------
@app.route('/')
def home():
   return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()

    if request.method == 'POST':
        # Verificación de reCAPTCHA
        recaptcha_response = request.form.get('g-recaptcha-response')
        payload = {
            'secret': RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
        result = r.json()

        if not result.get('success'):
            flash('reCAPTCHA falló. Inténtalo de nuevo.', 'danger')
            return redirect(url_for('login'))

        # Si pasa el reCAPTCHA, continua con el login
        email = request.form['email']
        password = request.form['password']
        
        # Manejo de excepciones al buscar usuario y controlar intentos fallidos
        try:
            user = User.query.filter_by(email=email).first()
            failed_attempt = FailedLoginAttempt.query.filter_by(email=email).first()

            current_time = int(time.time())

            if not failed_attempt:
                failed_attempt = FailedLoginAttempt(email=email, attempts=0, last_attempt=0)
                db.session.add(failed_attempt)
                db.session.commit()

            time_since_last_attempt = current_time - failed_attempt.last_attempt

            if failed_attempt.attempts >= MAX_ATTEMPTS:
                if time_since_last_attempt < BLOCK_TIME:
                    remaining_time = BLOCK_TIME - time_since_last_attempt
                    flash(f"Demasiados intentos fallidos. Inténtalo en {remaining_time} segundos.", "danger")
                    return redirect(url_for('login'))
                else:
                    failed_attempt.attempts = 0
                    failed_attempt.last_attempt = 0
                    db.session.commit()

            # Verificación de usuario y contraseña
            if user and user.check_password(password):
                login_user(user)
                print("Login exitoso, usuario:", user.username)  # Para verificar
                failed_attempt.attempts = 0
                failed_attempt.last_attempt = 0
                db.session.commit()
                flash("Inicio de sesión exitoso", "success")
                return redirect(url_for('dashboard'))
            else:
                failed_attempt.attempts += 1
                failed_attempt.last_attempt = current_time
                db.session.commit()
                flash("Usuario o contraseña incorrectos", "danger")

        except Exception as e:
            flash(f"Ocurrió un error: {str(e)}", 'danger')

    return render_template('login.html', form=form)

MAX_ATTEMPTS = 3
BLOCK_TIME = 15
RECAPTCHA_SECRET_KEY = '6LcUBSErAAAAAJm6VFJwH5cDPQvYGrFivu7_ef8T'  # Clave secreta de reCAPTCHA

@app.route('/dashboard')
@login_required
def dashboard():
    print("Usuario autenticado:", current_user.is_authenticated)  # Para verificar
    role = request.args.get('role', None)  # Por ejemplo, si lo recibes por query string
    return render_template('dashboard.html', user=current_user,  role=role)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente', 'info')
    return redirect(url_for('home'))

#------------------------------------------
#            ENDPOINT CREAR
#------------------------------------------

@app.route('/register/<role>', methods=['GET', 'POST'])
@login_required
def register(role):
    if current_user.role != UserRole.ADMIN:
        flash("No tienes permisos para crear usuarios.", "danger")
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password = form.password.data
        identificacion = form.identificacion.data

        # Verificar si ya existe un usuario con el mismo nombre de usuario
        if User.query.filter_by(username=username).first():
            flash("El usuario ya existe", "danger")
            return redirect(url_for('register', role=role))

        # Verificar si ya existe un usuario con la misma identificación en el mismo rol
        if User.query.filter_by(identificacion=identificacion, role=role).first():
            flash("Ya existe un usuario con esta identificación en el mismo rol.", "danger")
            return redirect(url_for('register', role=role))

        # Verificar que el rol sea válido
        if role not in ["administrativo", "candidato", "votante"]:
            flash("Rol inválido", "danger")
            return redirect(url_for('home'))

        # Crear nuevo usuario
        new_user = User(email=email, username=username, identificacion=identificacion, role=role)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Usuario registrado con éxito", "success")
        return redirect(url_for('login'))

    return render_template('register.html', form=form, role=role)


@app.route('/crear_eleccion', methods=['GET', 'POST'])
@login_required
def crear_eleccion():
    if current_user.role != UserRole.ADMIN:
        flash("Solo los administradores pueden crear elecciones.", "danger")
        return redirect(url_for('dashboard'))

    form = CrearEleccionForm()
    if form.validate_on_submit():
        nueva_eleccion = Eleccion(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            tipo_representacion=form.tipo_representacion.data,
            fecha_inicio=form.fecha_inicio.data,
            fecha_fin=form.fecha_fin.data,
            estado='programada'
        )
        db.session.add(nueva_eleccion)
        db.session.commit()
        flash("Elección creada exitosamente.", "success")
        return redirect(url_for('dashboard'))

    return render_template('crear_eleccion.html', form=form)


#------------------------------------------
#            ENDPOINT LISTAR
#------------------------------------------

@app.route('/listar_usuarios')
@login_required
def listar_usuarios():
    if current_user.role != UserRole.ADMIN:
        flash("Acceso denegado. Solo el administrador puede ver esta sección.", "danger")
        return redirect(url_for('dashboard'))

    search = request.args.get('search', '', type=str)
    role_filter = request.args.get('role', '', type=str)

    query = User.query.filter(User.id != current_user.id)

    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.identificacion.ilike(f"%{search}%"))
        )

    if role_filter:
        query = query.filter_by(role=UserRole(role_filter))

    users = query.all()

    return render_template('listar_usuarios.html', users=users, search=search, role_filter=role_filter)


# Ruta para ver la lista de elecciones
@app.route('/elecciones')
@login_required
def lista_elecciones():
    if current_user.role != UserRole.ADMIN:
        flash("Acceso denegado.", "danger")
        return redirect(url_for('dashboard'))

    now = datetime.now()
    elecciones = Eleccion.query.all()
    cambios = 0

    # Actualizar el estado de las elecciones
    for  e in elecciones:
        if e.fecha_inicio <= now <= e.fecha_fin and e.estado != 'activa':
            e.estado = 'activa'
            cambios += 1
        elif now > e.fecha_fin and e.estado != 'finalizada':
            e.estado = 'finalizada'
            cambios += 1
        elif now < e.fecha_inicio and e.estado != 'programada':
            e.estado = 'programada'
            cambios += 1

    if cambios > 0:
        db.session.commit()

    # Obtener parámetros de búsqueda y filtros
    tipo = request.args.get('tipo', '').strip()
    estado = request.args.get('estado', '').strip()
    busqueda = request.args.get('busqueda', '').strip()

    # Aplicar filtros
    query = Eleccion.query

    if tipo:
        query = query.filter(Eleccion.tipo_representacion == tipo)

    if estado:
        query = query.filter(Eleccion.estado == estado)

    if busqueda:
        query = query.filter(Eleccion.nombre.ilike(f"%{busqueda}%"))

    elecciones = query.order_by(desc(Eleccion.fecha_inicio)).all()

    return render_template('lista_elecciones.html', elecciones=elecciones)

@app.route('/resultados_elecciones')
@login_required
def resultados_elecciones():
    elecciones = Eleccion.query.all()
    return render_template('resultados_elecciones.html', elecciones=elecciones)  # Asegúrate de tener esta plantilla

@app.route('/resultados/<int:eleccion_id>')
@login_required
def ver_resultado_eleccion(eleccion_id):
    eleccion = Eleccion.query.get_or_404(eleccion_id)

    # Obtener candidaturas con sus votos
    candidaturas = Candidatura.query.filter_by(eleccionId=eleccion_id).all()
    
    resultados = []
    for c in candidaturas:
        perfil = c.user.profile
        nombres = perfil.nombres if perfil and perfil.nombres else c.user.username
        apellidos = perfil.apellidos if perfil and perfil.apellidos else ''
        resultados.append({
            'candidato': f"{nombres} {apellidos}".strip(),
            'username': c.user.username,
            'propuesta': c.propuesta,
            'votos': len(c.votos)
        })

    # Ordenar por número de votos descendente
    resultados.sort(key=lambda x: x['votos'], reverse=True)

    return render_template('ver_resultado_eleccion.html', eleccion=eleccion, resultados=resultados)

@app.route('/resultados/<int:eleccion_id>/print')
@login_required
def ver_resultado_eleccion_print(eleccion_id):
    eleccion = Eleccion.query.get_or_404(eleccion_id)
    candidaturas = Candidatura.query.filter_by(eleccionId=eleccion_id).all()

    resultados = []
    for c in candidaturas:
        perfil = c.user.profile
        nombres = perfil.nombres if perfil and perfil.nombres else c.user.username
        apellidos = perfil.apellidos if perfil and perfil.apellidos else ''
        resultados.append({
            'candidato': f"{nombres} {apellidos}".strip(),
            'username': c.user.username,
            'propuesta': c.propuesta,
            'votos': len(c.votos)
        })

    resultados.sort(key=lambda x: x['votos'], reverse=True)
    return render_template('ver_resultado_eleccion_print.html', eleccion=eleccion, resultados=resultados)


# Ruta para que los votantes vean las elecciones disponibles
@app.route('/votaciones_disponibles')
@login_required
def votaciones_disponibles():
    if current_user.role != UserRole.VOTANTE:
        flash("Acceso denegado", "danger")
        return redirect(url_for('dashboard'))

    ahora = datetime.now()
    elecciones = Eleccion.query.filter(Eleccion.estado == 'activa').all()
    elecciones = [e for e in elecciones if not Voto.query.filter_by(userId=current_user.id, eleccionId=e.id).first()]
    return render_template('votaciones_disponibles.html', elecciones=elecciones)

@app.route('/mis-votaciones')
@login_required
def mis_votaciones():
    if current_user.role != UserRole.VOTANTE:
        flash("Acceso denegado", "danger")
        return redirect(url_for('dashboard'))

    votos = Voto.query.filter_by(userId=current_user.id).all()
    return render_template('mis_votaciones.html', votos=votos)
#------------------------------------------
#            ENDPOINT ACTUALIZAR
#------------------------------------------
# Ruta para editar perfil
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # Lógica aquí para editar el perfil
    return render_template('edit_profile.html', user=current_user)

# Ruta para editar identificación (si es necesario)
@app.route('/edit_identificacion', methods=['GET', 'POST'])
@login_required
def edit_identificacion():
    # Lógica aquí para editar la identificación
    return render_template('edit_identificacion.html', user=current_user)


@app.route('/eleccion/<int:eleccion_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_eleccion(eleccion_id):
    if current_user.role != UserRole.ADMIN:
        flash("Acceso denegado.", "danger")
        return redirect(url_for('dashboard'))

    eleccion = Eleccion.query.get_or_404(eleccion_id)
    form = EditarEleccionForm(obj=eleccion)

    if form.validate_on_submit():
        eleccion.nombre = form.nombre.data
        eleccion.descripcion = form.descripcion.data
        eleccion.tipo_representacion = form.tipo_representacion.data
        eleccion.fecha_inicio = form.fecha_inicio.data
        eleccion.fecha_fin = form.fecha_fin.data

        now = datetime.now()
        estado_solicitado = form.estado.data
     
            # Calcular el estado que realmente debería tener según las fechas
        if eleccion.fecha_inicio <= now <= eleccion.fecha_fin:
            estado_esperado = 'activa'
        elif now > eleccion.fecha_fin:
            estado_esperado = 'finalizada'
        else:
            now < eleccion.fecha_inicio
            estado_esperado = 'programada'

        if estado_solicitado != estado_esperado:
            flash(f"⚠️ El estado solicitado '{estado_solicitado}' no es coherente con las fechas. "
                  f"Se ha actualizado automáticamente a '{estado_esperado}'.", "warning")
            eleccion.estado = estado_esperado
        else:
            eleccion.estado = estado_solicitado
            flash(f"Elección actualizada exitosamente", "success")

        db.session.commit()
        return redirect(url_for('lista_elecciones', eleccion_id=eleccion.id))

    return render_template('editar_eleccion.html', form=form, eleccion=eleccion)

# Ruta para cambiar la contraseña
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        # Lógica para cambiar la contraseña
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        # Aquí deberías implementar la lógica para verificar y actualizar la contraseña

        flash('Contraseña cambiada correctamente', 'success')
        return redirect(url_for('dashboard'))

    return render_template('change_password.html')  # Asegúrate de tener una plantilla para esta vista

# Ruta para votar en una elección
@app.route('/votar/<int:eleccion_id>', methods=['GET', 'POST'])
@login_required
def votar(eleccion_id):
    if current_user.role != UserRole.VOTANTE:
        flash("Acceso denegado", "danger")
        return redirect(url_for('dashboard'))

    eleccion = Eleccion.query.get_or_404(eleccion_id)
    candidatos = Candidatura.query.filter_by(eleccionId=eleccion_id).all()

    # Formulario vacío para CSRF protection
    form = VotarForm()

    voto_existente = Voto.query.filter_by(userId=current_user.id, eleccionId=eleccion_id).first()
    if voto_existente:
        flash("Ya has votado en esta elección", "info")
        return redirect(url_for('votaciones_disponibles'))

    if request.method == 'POST' and form.validate_on_submit():
        candidatura_id = int(request.form['candidatura_id'])

        nuevo_voto = Voto(
            userId=current_user.id,
            eleccionId=eleccion_id,
            candidaturaId=candidatura_id
        )
        db.session.add(nuevo_voto)
        db.session.commit()
        flash("✅ ¡Tu voto fue registrado exitosamente!", "success")
        return redirect(url_for('dashboard'))

    return render_template('votar.html', eleccion=eleccion, candidatos=candidatos, form=form)

#------------------------------------------
#            ENDPOINT ELIMINAR
#------------------------------------------

# Ruta para eliminar una elección
@app.route('/eleccion/<int:eleccion_id>/eliminar', methods=['POST'])
@login_required
def eliminar_eleccion(eleccion_id):
    if current_user.role != UserRole.ADMIN:
        flash("Acceso denegado. Solo el administrador puede eliminar elecciones.", "danger")
        return redirect(url_for('dashboard'))

    eleccion = Eleccion.query.get_or_404(eleccion_id)
    
    try:
        db.session.delete(eleccion)
        db.session.commit()
        flash("Elección eliminada exitosamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Ocurrió un error al eliminar la elección: {str(e)}", "danger")

    return redirect(url_for('lista_elecciones'))


#------------------------------------------
#            ENDPOINT LOGS
#------------------------------------------


@app.route('/logs_identificaciones', methods=['GET'])
@login_required
def logs_identificaciones():
    # Aquí deberías incluir la lógica para mostrar los logs de las identificaciones
    return render_template('logs_identificaciones.html')  # Asegúrate de tener esta plantilla creada

@app.route('/logs_elecciones', methods=['GET'])
@login_required
def logs_elecciones():
    # Aquí deberías incluir la lógica para mostrar los logs de las elecciones
    return render_template('logs_elecciones.html')  # Asegúrate de tener esta plantilla creada

#------------------------------------------



#------------------------------------------

if __name__ == '__main__':
    app.run(debug=True) 