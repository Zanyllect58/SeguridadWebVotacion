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
    # Lógica para crear una elección
    return render_template('crear_eleccion.html')  # Asegúrate de tener esta plantilla


#------------------------------------------
#            ENDPOINT LISTAR
#------------------------------------------
@app.route('/manage_users', methods=['GET'])
@login_required
def manage_users():
    # Lógica para gestionar usuarios (puedes cargar la lista de usuarios, etc.)
    return render_template('manage_users.html')  # Asegúrate de tener esta plantilla

@app.route('/listar_usuarios')
@login_required
def listar_usuarios():
    usuarios = User.query.all()
    
    usuarios_serializados = []
    for u in usuarios:
        usuario_dict = {
            'id': u.id,
            'identificacion': u.identificacion,
            'username': u.username,
            'email': u.email,
            'role': u.role.value,  # Serializamos el Enum como string legible
        }
        
        if u.profile:
            usuario_dict['profile'] = {
                'nombres': u.profile.nombres,
                'apellidos': u.profile.apellidos,
                'email': u.profile.email,
                'edad': u.profile.edad,
                'genero': u.profile.genero,
            }
        else:
            usuario_dict['profile'] = None

        usuarios_serializados.append(usuario_dict)

    return render_template('listar_usuarios.html', usuarios=usuarios_serializados)


@app.route('/lista_elecciones', methods=['GET'])
@login_required
def lista_elecciones():
    elecciones = Eleccion.query.all()
    role = current_user.role  # o donde tengas el rol del usuario
    return render_template("ver_elecciones.html", elecciones=elecciones, role=role)

@app.route('/resultados_elecciones')
@login_required
def resultados_elecciones():
    # Lógica para mostrar los resultados de las elecciones
    return render_template('resultados_elecciones.html')  # Asegúrate de tener esta plantilla



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

#------------------------------------------
#            ENDPOINT ELIMINAR
#------------------------------------------


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