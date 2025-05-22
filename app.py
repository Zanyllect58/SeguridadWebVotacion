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
from openpyxl import Workbook

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors

from reportlab.lib.utils import ImageReader
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

#------------------------------------------
#            ENDPOINT BASE
#------------------------------------------
@app.route('/')
def home():
   return render_template('index.html')
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
