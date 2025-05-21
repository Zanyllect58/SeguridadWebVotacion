from models import db, User, UserRole  
from app import app

with app.app_context():
    db.create_all()

    # Verifica si ya existe un usuario con ese username o esa identificación
    existing_user = User.query.filter(
        (User.username == "admin") | (User.identificacion == "000000001")
    ).first()
    
    if not existing_user:
        admin_user = User(
            identificacion="000000001",  # Identificación única para el admin
            username="admin",
            role=UserRole.ADMIN
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        db.session.commit()
        print("Usuario admin creado con éxito.")
    else:
        print("Ya existe un usuario con ese username o identificación.")
