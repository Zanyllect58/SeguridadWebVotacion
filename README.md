# README de Proyecto de Seguridad Web de Votación

## Descripción del Proyecto
Este proyecto es una aplicación web diseñada para gestionar procesos de votación de forma segura. Permite la creación, edición y visualización de elecciones, así como la gestión de usuarios.

## Estructura del Proyecto
La estructura de directorios se organiza de la siguiente manera:

```
/seguridadadwebvotacion
│
├── __pycache__/
│
├── templates/
│   ├── images/
│   │   └── Color_Vertical_2.png
│   ├── crear_eleccion.html
│   ├── dashboard.html
│   ├── editar_eleccion.html
│   ├── footer.html
│   ├── index.html
│   ├── lista_elecciones.html
│   ├── listar_usuarios.html
│   ├── login.html
│   ├── logs_elecciones.html
│   ├── mis_votaciones.html
│   ├── navbar.html
│   ├── register.html
│   ├── resultados_elecciones.html
│   ├── ver_resultado_eleccion_print.html
│   ├── ver_resultado_eleccion.html
│   └── votaciones_disponibles.html
│
├── uploads/
│   └── photos/
│       └── default.jpg
│
├── .gitignore
├── app.py
├── config.py
├── create_admin.py
├── forms.py
├── models.py
└── README.md
```

## Descripción de Archivos y Directorios

### Templates
- **images/**: Contiene imágenes utilizadas en la interfaz.
- **crear_eleccion.html**: HTML para crear una nueva elección.
- **dashboard.html**: Interfaz principal del usuario.
- **editar_eleccion.html**: Permite la edición de elecciones existentes.
- **footer.html**: Pie de página común para todas las plantillas.
- **index.html**: Página de inicio de la aplicación.
- **lista_elecciones.html**: Muestra la lista de elecciones disponibles.
- **listar_usuarios.html**: Muestra la lista de usuarios registrados.
- **login.html**: Página de inicio de sesión.
- **logs_elecciones.html**: Historial de logs de elecciones.
- **mis_votaciones.html**: Muestra las votaciones realizadas por el usuario.
- **navbar.html**: Barra de navegación común en toda la aplicación.
- **register.html**: Página de registro de nuevos usuarios.
- **resultados_elecciones.html**: Presenta los resultados de las elecciones.
- **ver_resultado_eleccion_print.html**: Plantilla para imprimir resultados de elecciones.
- **ver_resultado_eleccion.html**: Muestra el resultado específico de una elección.
- **votaciones_disponibles.html**: Muestra las votaciones en curso.

### Otros Archivos
- **.gitignore**: Archivos y carpetas que Git debe ignorar.
- **app.py**: Archivo principal que inicia la aplicación.
- **config.py**: Configuración de la aplicación.
- **create_admin.py**: Script para crear un usuario administrador.
- **forms.py**: Definición de formularios utilizados en la aplicación.
- **models.py**: Modelos de datos para la aplicación.
- **README.md**: Este documento que describe el proyecto.

## Instalación
1. Clona el repositorio.
2. Instala las dependencias necesarias.
3. Configura la base de datos.
4. Ejecuta `app.py` para iniciar la aplicación.

## Contribuciones
Las contribuciones son bienvenidas. Por favor, abre un issue o envía un pull request para discutir cambios.

## Licencia
Este proyecto está bajo la Licencia MIT. Para más detalles, consulta el archivo LICENSE.

---

¡Gracias por tu interés en el Proyecto de Seguridad Web de Votación!