import os
import time
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.exc import IntegrityError
import requests
from werkzeug.utils import secure_filename
from flask_reuploads import UploadSet, configure_uploads, IMAGES

from models import FailedLoginAttempt, IdentificationChangeLog, UserProfile, UserRole, Voto, db, User
from config import Config
from forms import ChangePasswordForm, EditIdentificacionForm, EditProfileForm, EditUserForm, EditarEleccionForm, LoginForm, RegisterForm
from flask import send_from_directory

from flask import send_file
from io import BytesIO
from openpyxl import Workbook

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors

import os


from forms import CrearEleccionForm
from models import Eleccion
from sqlalchemy import desc, func
from datetime import datetime


from models import Candidatura
from forms import AgregarCandidaturaForm
from forms import VotarForm
from dotenv import load_dotenv  # Importar dotenv para manejar variables de entorno

# Cargar variables de entorno
load_dotenv()

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
    if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
        flash("No tienes permisos para crear usuarios.", "danger")
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        email = form.email.data
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
        return redirect(url_for('lista_elecciones'))

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

    # Función para convertir cada usuario a dict
    def user_to_dict(user):
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'identificacion': user.identificacion,
            # Si role es un Enum, obtiene su valor, si no, lo convierte a string
            'role': user.role.value if hasattr(user.role, 'value') else str(user.role)
        }

    usuarios = [user_to_dict(u) for u in users]

    return render_template('listar_usuarios.html', usuarios=usuarios, search=search, role_filter=role_filter)

#Ruta para listar los votantes
@app.route('/listar_votantes')
@login_required
def listar_votantes():
    if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
        flash("Acceso denegado. Solo el administrador puede ver esta sección.", "danger")
        return redirect(url_for('dashboard'))

    search = request.args.get('search', '', type=str)

    # Solo usuarios con role votante
    query = User.query.filter(
        (User.id != current_user.id) &
        (User.role == UserRole.VOTANTE)
    )

    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.identificacion.ilike(f"%{search}%"))
        )

    users = query.all()

    def user_to_dict(user):
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'identificacion': user.identificacion,
            'role': user.role.value if hasattr(user.role, 'value') else str(user.role)
        }

    usuarios = [user_to_dict(u) for u in users]

    return render_template(
        'listar_usuarios.html',
        usuarios=usuarios,
        search=search,
        role_filter='votante',
        titulo='Lista de Votantes',
        mostrar_filtro=False
    )


# Ruta para ver la lista de elecciones
@app.route('/elecciones')
@login_required
def lista_elecciones():
    if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
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

@app.route('/eleccion/<int:eleccion_id>')
@login_required
def ver_eleccion(eleccion_id):
    if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO, UserRole.CANDIDATO]:
        flash("Acceso denegado. Solo el administrador, administrativo o el candidato puede ver detalles de elecciones.", "danger")
        return redirect(url_for('dashboard'))

    eleccion = Eleccion.query.get_or_404(eleccion_id)
    return render_template('ver_eleccion.html', eleccion=eleccion)

@app.route('/resultados_elecciones')
@login_required
def resultados_elecciones():
    if current_user.role == UserRole.CANDIDATO:
        candidaturas = Candidatura.query.filter_by(userId=current_user.id).all()
        elecciones = [c.eleccion for c in candidaturas]
        elecciones = list(set(elecciones))
    else:
        elecciones = Eleccion.query.filter(
            Eleccion.estado.in_(['activa', 'finalizada'])
        ).all()

    for eleccion in elecciones:
        resultados = (
            db.session.query(
                User.username.label("username"),
                UserProfile.profile_picture.label("profile_picture"),
                Candidatura.propuesta,
                func.count(Voto.id).label("votos"),
                User.id.label("user_id")
            )
            .join(Candidatura, Candidatura.id == Voto.candidaturaId)
            .join(User, User.id == Candidatura.userId)
            .outerjoin(UserProfile, User.identificacion == UserProfile.user_identificacion)
            .filter(Candidatura.eleccionId == eleccion.id)
            .group_by(User.id, Candidatura.propuesta, User.username, UserProfile.profile_picture)
            .order_by(func.count(Voto.id).desc())
            .all()
        )

        # Guardamos los resultados filtrados directamente en cada elección
        eleccion.resultados_filtrados = [r for r in resultados if r.votos > 0]

    return render_template('resultados_elecciones.html', elecciones=elecciones)



@app.route('/resultados/<int:eleccion_id>')
@login_required
def ver_resultado_eleccion(eleccion_id):
    eleccion = Eleccion.query.get_or_404(eleccion_id)

    # Obtener candidaturas con sus votos
    candidaturas = Candidatura.query.filter_by(eleccionId=eleccion_id).all()
    
    resultados = []
    total_votos = 0
    max_votos = 0
    votos_por_candidato = {}

    for c in candidaturas:
        perfil = c.user.profile
        nombres = perfil.nombres if perfil and perfil.nombres else c.user.username
        apellidos = perfil.apellidos if perfil and perfil.apellidos else ''
        votos_candidato = len(c.votos)
        total_votos += votos_candidato
        nombre_completo = f"{nombres} {apellidos}".strip()
        resultados.append({
            'candidato': nombre_completo,
            'username': c.user.username,
            'propuesta': c.propuesta,
            'votos': votos_candidato
        })
        votos_por_candidato[nombre_completo] = votos_candidato
        if votos_candidato > max_votos:
            max_votos = votos_candidato

    # Ordenar por número de votos descendente
    resultados.sort(key=lambda x: x['votos'], reverse=True)

    # Empate: contar cuántos tienen el máximo número de votos
    ganadores = [c for c in resultados if c['votos'] == max_votos]
    hubo_empate = len(ganadores) > 1

    return render_template('ver_resultado_eleccion.html',eleccion=eleccion, resultados=resultados,
                           total_votos=total_votos,hubo_empate=hubo_empate)


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

@app.route('/mis_votaciones')
@login_required
def mis_votaciones():
    if current_user.role != UserRole.VOTANTE:
        flash("Acceso denegado", "danger")
        return redirect(url_for('dashboard'))

    votos = Voto.query.filter_by(userId=current_user.id).all()
    return render_template('mis_votaciones.html', votos=votos)

#Ruta para gestionar los candidatos desde crear, listar

@app.route('/eleccion/<int:eleccion_id>/candidatos', methods=['GET', 'POST'])
@login_required
def gestionar_candidatos(eleccion_id):
    if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
        flash("Acceso denegado", "danger")
        return redirect(url_for('dashboard'))

    eleccion = Eleccion.query.get_or_404(eleccion_id)
    form = AgregarCandidaturaForm()
    
    # Opciones para seleccionar usuarios candidatos
    form.user_id.choices = [
        (u.id, f"{u.username} - ({u.identificacion})")
        for u in User.query.filter_by(role=UserRole.CANDIDATO).all()
    ]

    if form.validate_on_submit():
        # Validar si el candidato ya existe para esta elección
        existente = Candidatura.query.filter_by(
            userId=form.user_id.data,
            eleccionId=eleccion_id
        ).first()

        if existente:
            flash("⚠️ Este usuario ya está registrado como candidato en esta elección.", "warning")
        else:
            nueva = Candidatura(
                userId=form.user_id.data,
                eleccionId=eleccion_id,
                propuesta=form.propuesta.data
            )
            db.session.add(nueva)
            db.session.commit()
            flash("✅ Candidato agregado exitosamente", "success")
        return redirect(url_for('gestionar_candidatos', eleccion_id=eleccion_id))

    candidatos = Candidatura.query.filter_by(eleccionId=eleccion_id).all()
    return render_template('gestionar_candidatos.html', eleccion=eleccion, form=form, candidatos=candidatos)

#Ruta para listar elecciones de los candidatos
@app.route('/mis-elecciones')
@login_required
def mis_elecciones_candidato():
    if current_user.role.value != 'candidato':
        flash("Acceso denegado.", "danger")
        return redirect(url_for('dashboard'))

    # Obtener elecciones en las que participa el candidato actual
    elecciones = (
        db.session.query(Eleccion)
        .join(Candidatura, Candidatura.eleccionId == Eleccion.id)
        .filter(Candidatura.userId == current_user.id)
        .order_by(desc(Eleccion.fecha_inicio))
        .all()
    )

    return render_template('lista_elecciones.html', elecciones=elecciones)

#------------------------------------------
#            ENDPOINT ACTUALIZAR
#------------------------------------------

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()

    if not current_user.profile:
        current_user.profile = UserProfile(user_identificacion=current_user.identificacion)
        db.session.add(current_user.profile)
        db.session.commit()

    if form.validate_on_submit():
        if form.profile_picture.data:
            filename = secure_filename(form.profile_picture.data.filename)
            allowed_extensions = {'jpg', 'jpeg', 'png'}
            if filename.split('.')[-1].lower() not in allowed_extensions:
                flash('Formato de imagen no válido.', 'danger')
                return redirect(url_for('edit_profile'))

            upload_folder = app.config['UPLOADED_PHOTOS_DEST']
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            form.profile_picture.data.save(filepath)
            current_user.profile.profile_picture = filename

        # Asignar campos actualizados
        current_user.profile.nombres = form.nombres.data
        current_user.profile.apellidos = form.apellidos.data
        current_user.profile.edad = form.edad.data
        current_user.profile.genero = form.genero.data
        current_user.profile.bio = form.bio.data
        current_user.profile.language_preference = form.language_preference.data
        current_user.profile.notifications_enabled = form.notifications_enabled.data

        db.session.commit()
        flash('¡Perfil actualizado con éxito!', 'success')
        return redirect(url_for('dashboard'))

    # Prellenar formulario con datos existentes
    profile = current_user.profile
   
    form.nombres.data = profile.nombres
    form.apellidos.data = profile.apellidos
    form.edad.data = profile.edad
    form.genero.data = profile.genero
    form.bio.data = profile.bio
    form.language_preference.data = profile.language_preference
    form.notifications_enabled.data = profile.notifications_enabled

    return render_template('edit_profile.html', form=form)



@app.route('/admin/editar_usuario/<int:user_id>', methods=['GET', 'POST'])
@login_required
def editar_usuario_admin(user_id):
    if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
        flash("Acceso denegado.", "danger")
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)

    if request.method == 'GET':
        form.role.data = user.role.value  # Prellenar el rol

    if form.validate_on_submit():
        user.identificacion = form.identificacion.data
        user.username = form.username.data
        user.email = form.email.data

        if current_user.role == UserRole.ADMIN:
            user.role = UserRole(form.role.data)
        else:
            user.role = user.role

        try:
            db.session.commit()
            flash('Usuario actualizado correctamente.', 'success')
            if current_user.role == UserRole.ADMIN:
                return redirect(url_for('listar_usuarios'))
            else:
                return redirect(url_for('listar_votantes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el usuario: {e}', 'danger')

    return render_template('editar_usuario_admin.html', form=form, user=user, user_role=current_user.role.value)



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

@app.route('/edit_identificacion', methods=['GET', 'POST'])
@login_required
def edit_identificacion():
    form = EditIdentificacionForm()

    if form.validate_on_submit():
        nueva_identificacion = form.nueva_identificacion.data.strip()

        # Verifica si ya existe un usuario con esa identificación y mismo rol
        existing_user = User.query.filter_by(
            identificacion=nueva_identificacion,
            role=current_user.role
        ).first()

        if existing_user:
            flash('❌ Ya existe un usuario con esa identificación en el mismo rol.', 'danger')
            return redirect(url_for('edit_identificacion'))

        try:
            old_identificacion = current_user.identificacion
            current_user.identificacion = nueva_identificacion

            # Registrar el cambio en logs
            log = IdentificationChangeLog(
                changed_by_user_id=current_user.id,
                affected_user_id=current_user.id,
                old_identificacion=old_identificacion,
                new_identificacion=nueva_identificacion
            )

            db.session.add(log)
            db.session.commit()

            flash('✅ Identificación actualizada exitosamente.', 'success')
            return redirect(url_for('edit_profile'))

        except Exception as e:
            db.session.rollback()
            print(f"[Error] Falló la actualización: {e}")
            flash(f'⚠️ Ocurrió un error al actualizar: {str(e)}', 'danger')

    return render_template('edit_identificacion.html', form=form)


#Ruta para que el admin cambie su propia contraseña
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Contraseña actualizada exitosamente", "success")
        return redirect(url_for('edit_profile'))

    return render_template('change_password.html', form=form) # Asegúrate de tener una plantilla para esta vista

# Ruta para que el admin edite la contraseña de otros usuarios
@app.route('/edit_user_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_password_user(user_id):
    if current_user.role != UserRole.ADMIN:
        flash("No tienes permisos para editar contraseñas.", "danger")
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    form = ChangePasswordForm()

    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()
        flash(f"Contraseña de {user.username} actualizada", "success")
        return redirect(url_for('listar_usuarios'))

    return render_template('edit_user_password.html', form=form, user=user)


# Ruta para que el admin edite la identificación
@app.route('/edit_user_identificacion/<int:user_id>', methods=['GET', 'POST']) 
@login_required
def edit_identificacion_user(user_id):
    if current_user.role != UserRole.ADMIN:
        flash("Acceso denegado. Solo el administrador puede editar identificaciones.", "danger")
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    form = EditIdentificacionForm()

    if form.validate_on_submit():
        nueva_identificacion = form.nueva_identificacion.data

        existing_user = User.query.filter_by(identificacion=nueva_identificacion, role=user.role).first()
        if existing_user:
            flash('Ya existe un usuario con esa identificación en el mismo rol.', 'danger')
            return redirect(url_for('edit_user_identificacion', user_id=user.id))

        try:
            old_identificacion = user.identificacion
            user.identificacion = nueva_identificacion

            # Registrar el cambio en logs
            log = IdentificationChangeLog(
                changed_by_user_id=current_user.id,
                affected_user_id=user.id,
                old_identificacion=old_identificacion,
                new_identificacion=nueva_identificacion
            )
            
            db.session.add(log)
            db.session.commit()
            flash('Identificación del usuario actualizada exitosamente.', 'success')
            return redirect(url_for('listar_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al actualizar: {str(e)}', 'danger')
            
    return render_template('edit_user_identificacion.html', form=form, user=user)

# Ruta para editar una candidatura
@app.route('/candidatura/<int:candidatura_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_candidatura(candidatura_id):
    if current_user.role != UserRole.ADMIN:
        flash("Acceso denegado.", "danger")
        return redirect(url_for('dashboard'))

    candidatura = Candidatura.query.get_or_404(candidatura_id)
    eleccion_id = candidatura.eleccionId

    form = AgregarCandidaturaForm(obj=candidatura)

    # Obtener IDs ya usados, excepto el actual
    usados = db.session.query(Candidatura.userId).filter(
        Candidatura.eleccionId == eleccion_id,
        Candidatura.id != candidatura.id
    ).all()
    usados_ids = {uid for (uid,) in usados}

    # Armar opciones deshabilitadas si ya están en la elección
    choices = []
    for u in User.query.filter_by(role=UserRole.CANDIDATO).all():
        disabled = u.id in usados_ids
        choices.append((u.id, f"{u.username} - ({u.identificacion})", disabled))

    # Asignar choices al campo user_id (WTForms no permite directamente "disabled", así que lo pasamos a la vista)
    form.user_id.choices = [(id, label) for id, label, _ in choices]
    disabled_user_ids = [id for id, _, d in choices if d]

    form.user_id.data = candidatura.userId

    if form.validate_on_submit():
        duplicado = Candidatura.query.filter(
            Candidatura.userId == form.user_id.data,
            Candidatura.eleccionId == eleccion_id,
            Candidatura.id != candidatura.id
        ).first()

        if duplicado:
            flash("⚠️ Este usuario ya está registrado como candidato en esta elección.", "warning")
        else:
            candidatura.userId = form.user_id.data
            candidatura.propuesta = form.propuesta.data
            db.session.commit()
            flash("✅ Candidatura actualizada con éxito.", "success")
            return redirect(url_for('gestionar_candidatos', eleccion_id=eleccion_id))

    for field, errors in form.errors.items():
        for error in errors:
            flash(f"⚠️ {error}", "warning")

    return render_template('editar_candidatura.html', form=form, candidatura=candidatura, disabled_user_ids=disabled_user_ids)


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
@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != UserRole.ADMIN:
        flash("Acceso denegado. Solo el administrador puede eliminar usuarios.", "danger")
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("No puedes eliminar tu propia cuenta.", "warning")
        return redirect(url_for('manage_users'))

    try:
        #  Eliminar logs donde el usuario sea afectado o autor del cambio
        IdentificationChangeLog.query.filter(
            (IdentificationChangeLog.affected_user_id == user.id) |
            (IdentificationChangeLog.changed_by_user_id == user.id)
        ).delete(synchronize_session=False)


        db.session.delete(user)
        db.session.commit()
        flash(f"Usuario {user.username} eliminado exitosamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar usuario: {str(e)}", "danger")

    return redirect(url_for('listar_usuarios'))

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


# Ruta para eliminar una candidatura
@app.route('/candidatura/<int:candidatura_id>/eliminar', methods=['POST'])
@login_required
def eliminar_candidatura(candidatura_id):
    if current_user.role != UserRole.ADMIN:
        flash("Acceso denegado. Solo el administrador puede eliminar candidaturas.", "danger")
        return redirect(url_for('dashboard'))

    candidatura = Candidatura.query.get_or_404(candidatura_id)
    eleccion_id = candidatura.eleccionId

    try:
        db.session.delete(candidatura)
        db.session.commit()
        flash("Candidatura eliminada exitosamente.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("No se puede eliminar la candidatura porque tiene votos asociados.", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Ocurrió un error al eliminar la candidatura: {str(e)}", "danger")

    return redirect(url_for('gestionar_candidatos', eleccion_id=eleccion_id))
#------------------------------------------
#            ENDPOINT LOGS
#------------------------------------------


@app.route('/logs_identificaciones')
def logs_identificaciones():
    logs = IdentificationChangeLog.query.order_by(IdentificationChangeLog.timestamp.desc()).all()
    return render_template('logs_identificaciones.html', logs=logs)


@app.route('/test_create_log')
@login_required
def test_create_log():
    try:
        log = IdentificationChangeLog(
            changed_by_user_id=current_user.id,
            affected_user_id=current_user.id,
            old_identificacion='OLD123',
            new_identificacion='NEW123'
        )
        db.session.add(log)
        db.session.commit()
        return "Log creado correctamente"
    except Exception as e:
        db.session.rollback()
        return f"Error al crear log: {str(e)}"

#------------------------------------------
#            EXPORT
#------------------------------------------

@app.route('/export_logs_excel') # Ruta para exportar los logs a Excel
@login_required
def export_logs_excel():
    if current_user.role != UserRole.ADMIN:
        flash("Acceso denegado. Solo el administrador puede exportar los registros.", "danger")
        return redirect(url_for('dashboard'))

    logs = IdentificationChangeLog.query.order_by(IdentificationChangeLog.timestamp.desc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Cambios de Identificación"

    # Encabezados
    headers = ["#", "Usuario que hizo el cambio", "Usuario afectado", "Identificación anterior", "Identificación nueva", "Fecha y Hora"]
    ws.append(headers)

    # Filas
    for index, log in enumerate(logs, start=1):
        ws.append([
            index,
            log.changed_by.username,
            log.affected_user.username,
            log.old_identificacion,
            log.new_identificacion,
            log.timestamp.strftime('%d/%m/%Y %H:%M:%S')
        ])

    # Guardar en memoria
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="cambios_identificacion.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )




@app.route('/export_logs_pdf')
@login_required
def export_logs_pdf():
    if current_user.role != UserRole.ADMIN:
        flash("Acceso denegado. Solo el administrador puede exportar los registros.", "danger")
        return redirect(url_for('dashboard'))

    logs = IdentificationChangeLog.query.order_by(IdentificationChangeLog.timestamp.desc()).all()
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

   # Logo
    logo_path = os.path.join(app.root_path, 'static/images', 'logo.png')
    if os.path.exists(logo_path):
        c.drawImage(
        logo_path,
        x=2 * cm,
        y=height - 4.5 * cm,
        width=3 * cm,
        height=3 * cm,
        preserveAspectRatio=True,
        mask='auto'
    )

# Título alineado con el logo (justificado a la derecha del logo)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(6 * cm, height - 2.5 * cm, "Historial de Cambios de Identificación")

# Subtítulo institucional bajo el título principal
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(colors.darkgray)
    c.drawString(6 * cm, height - 3.2 * cm, "Sistema de Votación Electrónica - USTA ")
    c.setFillColor(colors.black)  # Restablece color para lo demás


    #  Luego inicia la tabla
    c.setFont("Helvetica", 9)
    y = height - 5.2 * cm
    line_height = 1 * cm
    headers = ["#", "Cambió", "Afectado", "Antes", "Ahora", "Fecha y Hora"]
    col_positions = [1.5, 3.5, 7.0, 10.0, 12.5, 15.0]

    def draw_table_header(y_pos):
        c.setFillColor(colors.whitesmoke)
        c.rect(1.5 * cm, y_pos - 0.3 * cm, width - 3 * cm, 0.7 * cm, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        for i, header in enumerate(headers):
            c.drawString(col_positions[i] * cm, y_pos, header)

    def draw_footer(page_num):
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(colors.grey)
        c.drawRightString(width - 2 * cm, 1.5 * cm, f"Página {page_num}")
        c.drawString(2 * cm, 1.5 * cm, "Generado por el Sistema de Votación - USTA - Tunja 2025")

    page_num = 1
    draw_table_header(y)
    y -= line_height

    c.setFont("Helvetica", 9)
    for i, log in enumerate(logs, start=1):
        if y < 3 * cm:
            draw_footer(page_num)
            c.showPage()
            page_num += 1
            y = height - 5.2 * cm
            draw_table_header(y)
            y -= line_height

        if i % 2 == 0:
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(1.5 * cm, y - 0.3 * cm, width - 3 * cm, 0.7 * cm, fill=1)
        c.setFillColor(colors.black)

        row = [
            str(i),
            log.changed_by.username,
            log.affected_user.username,
            log.old_identificacion,
            log.new_identificacion,
            log.timestamp.strftime('%d/%m/%Y %H:%M')
        ]
        for j, text in enumerate(row):
            c.drawString(col_positions[j] * cm, y, text)
        y -= line_height

    draw_footer(page_num)
    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="cambios_identificacion.pdf",
        mimetype='application/pdf'
    )



if __name__ == '__main__':
    app.run(debug=True) 