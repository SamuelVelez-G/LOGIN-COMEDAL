"""Capa de presentación: rutas, sesión y vistas. Sin SQL ni reglas de negocio."""

import hmac
import os
import secrets
from datetime import timedelta
from functools import wraps

from flask import (
    Flask, abort, flash, redirect, render_template,
    request, session, url_for,
)

import auth
import database as db

app = Flask(__name__)

# En producción la clave viene del entorno; el respaldo aleatorio permite
# ejecutar la app sin configuración previa.
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

app.config.update(
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=15),
    SESSION_COOKIE_HTTPONLY=True,    # inaccesible desde JavaScript
    SESSION_COOKIE_SAMESITE="Lax",
    # SESSION_COOKIE_SECURE=True,    # activar bajo HTTPS
)


# --- CSRF ---------------------------------------------------------
def obtener_token_csrf():
    """Token único por sesión para el formulario."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def validar_token_csrf():
    """Comparación en tiempo constante para no filtrar por temporización."""
    enviado = request.form.get("csrf_token", "")
    esperado = session.get("csrf_token", "")
    if not esperado or not hmac.compare_digest(enviado, esperado):
        abort(400, description="Token de seguridad inválido. Recargue la página.")


app.jinja_env.globals["csrf_token"] = obtener_token_csrf


# --- Control de acceso --------------------------------------------
def login_requerido(vista):
    """Protege rutas privadas desde un único punto."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "id_asociado" not in session:
            flash("Debe iniciar sesión para acceder a esta sección.", "aviso")
            return redirect(url_for("login"))
        return vista(*args, **kwargs)
    return envoltura


@app.before_request
def renovar_sesion():
    """Reinicia el contador de inactividad."""
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)


@app.after_request
def cabeceras_seguridad(respuesta):
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"       # clickjacking
    respuesta.headers["Referrer-Policy"] = "same-origin"
    respuesta.headers["Cache-Control"] = "no-store"     # datos privados
    return respuesta


# --- Rutas --------------------------------------------------------
@app.route("/")
def inicio():
    if "id_asociado" in session:
        return redirect(url_for("panel"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "id_asociado" in session:
        return redirect(url_for("panel"))

    if request.method == "POST":
        validar_token_csrf()

        identificador = request.form.get("identificador", "")
        password = request.form.get("password", "")

        exito, mensaje, asociado = auth.autenticar(
            identificador, password, request.remote_addr
        )

        if not exito:
            flash(mensaje, "error")
            # Se devuelve el identificador, nunca la contraseña.
            return render_template("login.html", identificador=identificador)

        session.clear()   # previene fijación de sesión
        session["id_asociado"] = asociado["id_asociado"]
        session["nombre"] = asociado["nombre"]
        session.permanent = True

        return redirect(url_for("panel"))

    return render_template("login.html", identificador="")


@app.route("/panel")
@login_requerido
def panel():
    id_asociado = session["id_asociado"]

    asociado = db.obtener_asociado_por_id(id_asociado)
    if asociado is None:
        session.clear()
        flash("La sesión ya no es válida.", "error")
        return redirect(url_for("login"))

    resumen = db.obtener_resumen_financiero(id_asociado)
    productos = db.obtener_productos(id_asociado)
    eventos = db.obtener_ultimos_eventos(id_asociado, 5)

    return render_template(
        "panel.html",
        asociado=asociado,
        cedula_enmascarada=auth.enmascarar_cedula(asociado["cedula"]),
        correo_enmascarado=auth.enmascarar_correo(asociado["correo"]),
        resumen=resumen,
        productos=productos,
        eventos=eventos,
        posicion_neta=resumen["total_ahorros"] - resumen["total_deuda"],
    )


@app.route("/logout")
def logout():
    id_asociado = session.get("id_asociado")
    if id_asociado:
        asociado = db.obtener_asociado_por_id(id_asociado)
        db.registrar_evento(
            asociado["usuario"] if asociado else "desconocido",
            "LOGOUT",
            id_asociado,
            request.remote_addr,
        )

    session.clear()   # destruye la sesión completa, no una clave
    flash("Su sesión se cerró correctamente.", "aviso")
    return redirect(url_for("login"))


# --- Errores ------------------------------------------------------
@app.errorhandler(404)
def no_encontrado(error):
    return render_template("error.html",
                           codigo=404,
                           mensaje="La página solicitada no existe."), 404


@app.errorhandler(400)
def peticion_invalida(error):
    return render_template("error.html",
                           codigo=400,
                           mensaje=getattr(error, "description",
                                           "La solicitud no es válida.")), 400


@app.errorhandler(500)
def error_interno(error):
    # Sin detalle técnico hacia el usuario final.
    return render_template("error.html",
                           codigo=500,
                           mensaje="Ocurrió un error inesperado."), 500



@app.template_filter("pesos")
def formato_pesos(valor):
    return f"${valor:,.0f}".replace(",", ".")


if __name__ == "__main__":
    # debug solo en desarrollo; en producción, servidor WSGI.
    app.run(debug=True, port=5000)