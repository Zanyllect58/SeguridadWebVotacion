from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed  # Importar FileField y FileAllowed para subida de archivos 
from wtforms.fields import DateTimeLocalField, SelectField
from wtforms import ValidationError
from datetime import datetime
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from models import Candidatura
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf.file import FileField, FileAllowed



class LoginForm(FlaskForm): # Formulario de inicio de sesión
    #username = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=50)])
    email = StringField('Eamil', validators=[DataRequired(), Length(min=4, max=50)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

class RegisterForm(FlaskForm):
    identificacion = StringField('Identificación', validators=[DataRequired(), Length(min=5, max=20)])  # NUEVO CAMPO
    username = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=50)])
    email =  StringField('Email', validators=[DataRequired(), Length(min=4, max=60)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Registrar')


class EditProfileForm(FlaskForm):
    nombres = StringField('Nombres', validators=[DataRequired(), Length(max=255)])
    apellidos = StringField('Apellidos', validators=[DataRequired(), Length(max=255)])
    email = StringField('Email', validators=[DataRequired(), Length(max=255)])
    edad = IntegerField('Edad', validators=[NumberRange(min=0, max=120)])
    genero = SelectField('Género', choices=[
        ('masculino', 'Masculino'),
        ('femenino', 'Femenino'),
        ('otro', 'Otro')
    ], validators=[DataRequired()])
    bio = TextAreaField('Biografía', validators=[Length(max=500)])
    profile_picture = FileField('Imagen de perfil', validators=[FileAllowed(['jpg', 'png', 'jpeg'], '¡Solo imágenes válidas!')])
    language_preference = SelectField('Idioma', choices=[
        ('es', 'Español'),
        ('en', 'Inglés')
    ], validators=[DataRequired()])
    notifications_enabled = BooleanField('Recibir notificaciones')
    submit = SubmitField('Guardar cambios')


class ChangePasswordForm(FlaskForm):
    new_password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Actualizar Contraseña')

class EditIdentificacionForm(FlaskForm):
    nueva_identificacion = StringField('Nueva Identificación', validators=[DataRequired(), Length(min=5, max=20)])
    submit = SubmitField('Actualizar Identificación')



class CrearEleccionForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción')
    tipo_representacion = SelectField(
        'Tipo de Representación',
        choices=[('', '-- Selecciona --'), ('facultad', 'Facultad'), ('semestre', 'Semestre'), ('comite', 'Comité')],
        validators=[DataRequired()]
    )
    fecha_inicio = DateTimeLocalField('Fecha de Inicio', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    fecha_fin = DateTimeLocalField('Fecha de Fin', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Crear Elección')

      
    def validate_fecha_inicio(self, field):
        now = datetime.now()
        if field.data < now:
            raise ValidationError('La fecha de inicio no puede estar en el pasado.')
    

    def validate_fecha_fin(self, field):
        if self.fecha_inicio.data and field.data <= self.fecha_inicio.data:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')

class EditarEleccionForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción')
    tipo_representacion = SelectField(
        'Tipo de Representación',
        choices=[('', '-- Selecciona --'), ('facultad', 'Facultad'), ('semestre', 'Semestre'), ('comite', 'Comité')],
        validators=[DataRequired()]
    )
    fecha_inicio = DateTimeLocalField('Fecha de Inicio', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    fecha_fin = DateTimeLocalField('Fecha de Fin', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    estado = SelectField('Estado', choices=[
        ('programada', 'Programada'),
        ('activa', 'Activa'),
        ('finalizada', 'Finalizada')
    ], validators=[DataRequired()])
    submit = SubmitField('Guardar Cambios')

    def validate_fecha_inicio(self, field):
        now = datetime.now()
        
    def validate_fecha_fin(self, field):
        if self.fecha_inicio.data and field.data <= self.fecha_inicio.data:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        

class AgregarCandidaturaForm(FlaskForm):
    user_id = SelectField('Seleccionar Usuario', coerce=int, validators=[DataRequired()])
    propuesta = TextAreaField('Propuesta', validators=[DataRequired()])
    submit = SubmitField('Agregar Candidato')

    def __init__(self, eleccion_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eleccion_id = eleccion_id

    def validate_user_id(self, field):
        if self.eleccion_id is not None:
            existente = Candidatura.query.filter_by(userId=field.data, eleccionId=self.eleccion_id).first()
            if existente:
                raise ValidationError("Este usuario ya está registrado como candidato en esta elección.")


class VotarForm(FlaskForm):
    pass
