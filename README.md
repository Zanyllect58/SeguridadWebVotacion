# Proyecto de Aplicación Web de Votación

## Descripción

Este repositorio contiene una aplicación web diseñada para la gestión de elecciones y votaciones. Permite a los usuarios registrarse, crear elecciones, votar y ver los resultados en tiempo real.

## Estructura del Proyecto

### Directorio `templates`

Contiene los archivos HTML utilizados para renderizar las vistas de la aplicación.

- **images**
    - `crear_eleccion.html`: Página para crear una nueva elección.
    - `dashboard.html`: Tablero principal de la aplicación.
    - `edit_profile.html`: Formulario para editar el perfil del usuario.
    - `edit_user_password.html`: Formulario para cambiar la contraseña del usuario.
    - `editar_candidatura.html`: Página para editar la candidatura.
    - `editar_eleccion.html`: Página para editar una elección existente.
    - `editar_usuario_admin.html`: Página para editar los detalles del usuario administrador.
    - `gestion_candidatos.html`: Gestión de candidatos en una elección.
    - `index.html`: Página de inicio de la aplicación.
    - `lista_elecciones.html`: Lista de elecciones disponibles.
    - `listar_usuarios.html`: Listado de usuarios registrados.
    - `login.html`: Página de inicio de sesión.
    - `logs_identificaciones.html`: Registro de identificaciones de usuarios.
    - `logs_votaciones.html`: Registro de votaciones.
    - `mis_votaciones.html`: Página donde los usuarios pueden ver sus votaciones.
    - `navbar.html`: Barra de navegación común.
    - `register.html`: Página para el registro de nuevos usuarios.
    - `resultados_elecciones.html`: Página de resultados de elecciones.
    - `ver_eleccion.html`: Visualizar detalles de una elección específica.
    - `ver_resultado_eleccion_print.html`: Vista para imprimir resultados de elecciones.
    - `ver_resultado_eleccion.html`: Visualización de resultados de elecciones.
    - `votaciones_disponibles.html`: Página que muestra elecciones disponibles para votar.
    - `votar.html`: Página para realizar una votación.

### Directorio `uploads`

Contiene archivos subidos por los usuarios.

### Archivos Principales

- `app.py`: Archivo principal de la aplicación donde se define la lógica y configuración del servidor.
- `config.py`: Configuración de la aplicación, incluyendo las credenciales de la base de datos y otras variables de entorno.
- `create_admin.py`: Script para crear un usuario administrador inicial.
- `forms.py`: Definición de los formularios utilizados en la aplicación.
- `models.py`: Definición de los modelos de datos para la base de datos.
- `README.md`: Este archivo de documentación.

## Requisitos

- Python 3.x
- Flask
- Otras dependencias especificadas en `requirements.txt`.

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. Instalar las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Configurar la base de datos y las variables de entorno.

4. Ejecutar la aplicación:
   ```bash
   python app.py
   ```

## Contribución

Las contribuciones son bienvenidas. Por favor, enviar un pull request o abrir un issue para discutir los cambios propuestos.

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo LICENSE para más detalles.

--- 

¡Sigue estas instrucciones para iniciar y utilizar la aplicación de votaciones exitosamente!