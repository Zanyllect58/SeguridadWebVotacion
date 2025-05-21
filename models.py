from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import enum
from datetime import datetime


db = SQLAlchemy()

# Definir Enum para los roles
class UserRole(enum.Enum):
    ADMIN = "admin"
    ADMINISTRATIVO = "administrativo"
    CANDIDATO = "candidato"
    VOTANTE = "votante"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    identificacion = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.CANDIDATO, nullable=False)

    profile = db.relationship( # Relación uno a uno para el perfil y el usuario
        'UserProfile', # Relación uno a uno para el perfil y el usuario
        uselist=False, # Relación uno a uno para el perfil y el usuario  
        back_populates='user', # Relación uno a uno para el perfil
        cascade="all, delete-orphan", # Permite eliminar el perfil si se elimina el usuario 
        primaryjoin="User.identificacion == UserProfile.user_identificacion" # Relación uno a uno
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    __table_args__ = (
    db.UniqueConstraint('identificacion', 'role', name='uq_identificacion_role'),
)


class FailedLoginAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    attempts = db.Column(db.Integer, default=0)
    last_attempt = db.Column(db.Integer, default=0)


class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_identificacion = db.Column(
        db.String(20),
        db.ForeignKey('user.identificacion', onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    nombres = db.Column(db.String(255), nullable=True)
    apellidos = db.Column(db.String(255), nullable=True)
    edad = db.Column(db.Integer, nullable=True)
    genero = db.Column(db.Enum('masculino', 'femenino', 'otro'), nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    language_preference = db.Column(db.String(255), nullable=True)
    notifications_enabled = db.Column(db.Boolean, default=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship(
        'User',
        back_populates='profile',
        foreign_keys=[user_identificacion],
        primaryjoin="UserProfile.user_identificacion == User.identificacion"
    )

    def __repr__(self):
        return f"<UserProfile {self.user.username}>"

from datetime import datetime

class IdentificationChangeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    affected_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    old_identificacion = db.Column(db.String(20), nullable=False)
    new_identificacion = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    changed_by = db.relationship('User', foreign_keys=[changed_by_user_id], backref='changes_made')
    affected_user = db.relationship('User', foreign_keys=[affected_user_id], backref='changes_received')

    def __repr__(self):
        return f"<Log {self.timestamp} | {self.changed_by.username} cambió {self.old_identificacion} → {self.new_identificacion}>"

class Eleccion(db.Model):
    __tablename__ = 'eleccions'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    tipo_representacion = db.Column(db.Enum('facultad', 'semestre', 'comite'), nullable=False)
    fecha_inicio = db.Column(db.DateTime, nullable=False)
    fecha_fin = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.Enum('activa', 'finalizada', 'programada'), default='programada', nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Candidatura(db.Model):
    __tablename__ = 'candidaturas'

    id = db.Column(db.Integer, primary_key=True)
    propuesta = db.Column(db.Text, nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    userId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    eleccionId = db.Column(db.Integer, db.ForeignKey('eleccions.id'), nullable=False)

    user = db.relationship('User', backref='candidaturas')
    eleccion = db.relationship('Eleccion', backref='candidaturas')

class Voto(db.Model):
    __tablename__ = 'votos'

    id = db.Column(db.Integer, primary_key=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    userId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    eleccionId = db.Column(db.Integer, db.ForeignKey('eleccions.id'), nullable=False)
    candidaturaId = db.Column(db.Integer, db.ForeignKey('candidaturas.id'), nullable=False)

    user = db.relationship('User', backref='votos_emitidos')
    eleccion = db.relationship('Eleccion', backref='votos')
    candidatura = db.relationship('Candidatura', backref='votos')
