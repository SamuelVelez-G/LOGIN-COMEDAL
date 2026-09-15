# Portal de asociados — Prueba técnica

Aplicación web de autenticación con almacenamiento local, desarrollada en
Python (Flask) y SQLite.

Permite iniciar sesión con usuario o correo, valida las credenciales contra
datos almacenados localmente, da acceso a una sección privada y permite
cerrar sesión. El caso se ambientó en un portal de una cooperativa de ahorro
y crédito: al ingresar, el asociado consulta sus saldos y la actividad
reciente de su cuenta.

## Ejecución

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1      # Windows
# source venv/bin/activate       # Linux / macOS

pip install -r requirements.txt
python init_db.py
python app.py
```

Abrir <http://127.0.0.1:5000>

No requiere instalar ningún motor de base de datos.

### Credenciales de prueba

| Usuario | Correo | Contraseña |
|---|---|---|
| `arestrepo` | ana.restrepo@correo.com | `Comedal2026*` |
| `cgomez` | carlos.gomez@correo.com | `Medellin2026*` |
| `lospina` | luisa.ospina@correo.com | `Antioquia2026*` |

### Verificación

```bash
python verificar_datos.py       # acceso a datos e intento de inyección SQL
python verificar_seguridad.py   # autenticación, bloqueo y enmascaramiento
```

Ambos scripts modifican datos de prueba; regenerar luego con `python init_db.py`.

## Estructura

```
app.py          Rutas, sesión y vistas
auth.py         Reglas de autenticación
database.py     Consultas SQL
schema.sql      Esquema relacional
init_db.py      Creación de la base y datos de prueba
templates/      Vistas Jinja2
static/css/     Estilos
```

Arquitectura en capas: el SQL vive solo en `database.py`, las reglas de
negocio solo en `auth.py`, y `app.py` se limita a traducir peticiones HTTP.
`auth.py` no importa Flask, por lo que la lógica de seguridad se puede probar
sin levantar el servidor.


## Seguridad

- Contraseñas almacenadas como hash.
- Mismo mensaje de error para usuario inexistente y contraseña incorrecta, y
  tiempo de respuesta equivalente en ambos casos, para no permitir enumerar
  usuarios.
- Bloqueo temporal de 15 minutos tras 5 intentos fallidos.
- Sesión con expiración por inactividad
- Token CSRF en el formulario.

## Protección de datos

Alineado con la Ley 1581 de 2012: se almacenan solo los datos necesarios, el
documento y el correo se muestran enmascarados, y el titular puede ver el
registro de accesos a su cuenta. Los datos incluidos son ficticios.

## Fuera de alcance

Para un entorno productivo faltarían: `SECRET_KEY` en variable de entorno,
HTTPS con `SESSION_COOKIE_SECURE`, servidor WSGI con `debug=False`, política
de contraseñas y recuperación, segundo factor, límite de peticiones por IP,
roles y permisos, y pruebas automatizadas con `pytest`.
