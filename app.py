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




MAX_ATTEMPTS = 3
BLOCK_TIME = 15
RECAPTCHA_SECRET_KEY = '6LfzLRsrAAAAALyqQGFcF0LFAHBPavE_lqE0yAhD'  # Clave secreta de reCAPTCHA

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
        # Verificación reCAPTCHA
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
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        failed_attempt = FailedLoginAttempt.query.filter_by(username=username).first()

        current_time = int(time.time())

        if not failed_attempt:
            failed_attempt = FailedLoginAttempt(username=username, attempts=0, last_attempt=0)
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

        if user and user.check_password(password):
            login_user(user)
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

    return render_template('login.html', form=form)
#------------------------------------------
#            ENDPOINT CREAR
#------------------------------------------

#------------------------------------------
#            ENDPOINT LISTAR
#------------------------------------------

#------------------------------------------
#            ENDPOINT ACTUALIZAR
#------------------------------------------

#------------------------------------------
#            ENDPOINT ELIMINAR
#------------------------------------------


#------------------------------------------
#            ENDPOINT LOGS
#------------------------------------------




#------------------------------------------



#------------------------------------------

if __name__ == '__main__':
    app.run(debug=True) 