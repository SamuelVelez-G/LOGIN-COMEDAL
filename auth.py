"""Lógica de autenticación. No depende de Flask ni de HTTP."""

from werkzeug.security import check_password_hash, generate_password_hash

import database as db

# Mismo mensaje para todo fallo: evita enumerar usuarios existentes.
MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos."

# Señuelo para igualar el tiempo de respuesta cuando el usuario no existe.
_HASH_SENUELO = generate_password_hash("hash_senuelo_sin_uso_real")


def autenticar(identificador, password, ip_origen=None):
    """
    Valida usuario/correo y contraseña.
    Devuelve (exito, mensaje, asociado).
    """
    identificador = (identificador or "").strip()

    if not identificador or not password:
        return False, "Debe ingresar usuario y contraseña.", None

    asociado = db.buscar_asociado_por_identificador(identificador)

    if asociado is None:
        # Consume tiempo equivalente al de una verificación real.
        check_password_hash(_HASH_SENUELO, password)
        db.registrar_evento(identificador, "LOGIN_FALLIDO", None, ip_origen)
        return False, MENSAJE_CREDENCIALES, None

    bloqueado, minutos = db.esta_bloqueado(asociado)
    if bloqueado:
        db.registrar_evento(
            identificador, "CUENTA_BLOQUEADA", asociado["id_asociado"], ip_origen
        )
        mensaje = (
            f"Cuenta bloqueada temporalmente por intentos fallidos. "
            f"Intente nuevamente en {minutos} minuto(s)."
        )
        return False, mensaje, None

    if asociado["estado"] != "ACTIVO":
        db.registrar_evento(
            identificador, "LOGIN_FALLIDO", asociado["id_asociado"], ip_origen
        )
        return False, "La cuenta no se encuentra activa. Comuníquese con la Cooperativa.", None

    if not check_password_hash(asociado["password_hash"], password):
        quedo_bloqueada = db.registrar_intento_fallido(asociado["id_asociado"])
        db.registrar_evento(
            identificador, "LOGIN_FALLIDO", asociado["id_asociado"], ip_origen
        )

        if quedo_bloqueada:
            return False, (
                f"Cuenta bloqueada temporalmente tras "
                f"{db.MAX_INTENTOS_FALLIDOS} intentos fallidos. "
                f"Intente nuevamente en {db.MINUTOS_BLOQUEO} minutos."
            ), None

        return False, MENSAJE_CREDENCIALES, None

    db.registrar_acceso_exitoso(asociado["id_asociado"])
    db.registrar_evento(
        identificador, "LOGIN_EXITOSO", asociado["id_asociado"], ip_origen
    )
    return True, "", asociado


def enmascarar_cedula(cedula):
    """Oculta los dígitos centrales del documento (Ley 1581 de 2012)."""
    if not cedula or len(cedula) < 5:
        return "****"
    return f"{cedula[:2]}{'*' * (len(cedula) - 5)}{cedula[-3:]}"


def enmascarar_correo(correo):
    """Oculta parte del correo: an**********@correo.com"""
    if not correo or "@" not in correo:
        return "****"
    usuario, dominio = correo.split("@", 1)
    if len(usuario) <= 2:
        return f"{usuario[0]}***@{dominio}"
    return f"{usuario[:2]}{'*' * (len(usuario) - 2)}@{dominio}"