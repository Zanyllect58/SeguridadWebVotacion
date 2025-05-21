import os # Importamos la librería os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'una_clave_secreta_segura') # Clave secreta para proteger los datos de la aplicación
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/voting_flask_db_project' # URI de la base de datos
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Deshabilitar las notificaciones de cambios en la base de datos
