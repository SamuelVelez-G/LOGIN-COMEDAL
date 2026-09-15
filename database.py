"""
Capa de acceso a datos. Todo el SQL de la aplicación vive aquí.
Las consultas son parametrizadas: la entrada del usuario nunca se concatena.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

RUTA_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comedal.db")

# Política de bloqueo por intentos fallidos
MAX_INTENTOS_FALLIDOS = 5
MINUTOS_BLOQUEO = 15

FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


# ------------------------------------------------------------------
# Conexión
# ------------------------------------------------------------------
@contextmanager
def obtener_conexion():
    """Conexión con commit/rollback y cierre garantizado."""
    conexion = sqlite3.connect(RUTA_DB)
    conexion.row_factory = sqlite3.Row      # acceso por nombre de columna
    conexion.execute("PRAGMA foreign_keys = ON")   # SQLite las trae apagadas
    try:
        yield conexion
        conexion.commit()
    except sqlite3.Error:
        conexion.rollback()
        raise
    finally:
        conexion.close()


# ------------------------------------------------------------------
# Consultas de asociados
# ------------------------------------------------------------------
def buscar_asociado_por_identificador(identificador):
    """Busca por nombre de usuario o por correo. Devuelve Row o None."""
    consulta = """
        SELECT id_asociado, cedula, nombre, usuario, correo,
               password_hash, estado, intentos_fallidos, bloqueado_hasta
        FROM asociados
        WHERE usuario = ? OR correo = ?
    """
    with obtener_conexion() as conexion:
        return conexion.execute(
            consulta,
            (identificador, identificador),
        ).fetchone()


def obtener_asociado_por_id(id_asociado):
    consulta = """
        SELECT id_asociado, cedula, nombre, usuario, correo, estado, ultimo_acceso
        FROM asociados
        WHERE id_asociado = ?
    """
    with obtener_conexion() as conexion:
        return conexion.execute(consulta, (id_asociado,)).fetchone()


# ------------------------------------------------------------------
# Control de intentos fallidos y bloqueo
# ------------------------------------------------------------------
def esta_bloqueado(asociado):
    """Devuelve (bloqueado, minutos_restantes)."""
    if not asociado["bloqueado_hasta"]:
        return False, 0

    limite = datetime.strptime(asociado["bloqueado_hasta"], FORMATO_FECHA)
    ahora = datetime.now()

    if ahora < limite:
        restantes = int((limite - ahora).total_seconds() // 60) + 1
        return True, restantes

    return False, 0


def registrar_intento_fallido(id_asociado):
    """Suma un intento fallido. Devuelve True si la cuenta quedó bloqueada."""
    with obtener_conexion() as conexion:
        conexion.execute(
            """
            UPDATE asociados
            SET intentos_fallidos = intentos_fallidos + 1
            WHERE id_asociado = ?
            """,
            (id_asociado,),
        )

        intentos = conexion.execute(
            "SELECT intentos_fallidos FROM asociados WHERE id_asociado = ?",
            (id_asociado,),
        ).fetchone()["intentos_fallidos"]

        if intentos >= MAX_INTENTOS_FALLIDOS:
            hasta = (datetime.now()
                     + timedelta(minutes=MINUTOS_BLOQUEO)).strftime(FORMATO_FECHA)
            conexion.execute(
                """
                UPDATE asociados
                SET bloqueado_hasta = ?, intentos_fallidos = 0
                WHERE id_asociado = ?
                """,
                (hasta, id_asociado),
            )
            return True

    return False


def registrar_acceso_exitoso(id_asociado):
    """Reinicia contadores y actualiza el último acceso."""
    ahora = datetime.now().strftime(FORMATO_FECHA)
    with obtener_conexion() as conexion:
        conexion.execute(
            """
            UPDATE asociados
            SET intentos_fallidos = 0,
                bloqueado_hasta   = NULL,
                ultimo_acceso     = ?
            WHERE id_asociado = ?
            """,
            (ahora, id_asociado),
        )


# ------------------------------------------------------------------
# Productos del asociado (sección privada)
# ------------------------------------------------------------------
def obtener_productos(id_asociado):
    consulta = """
        SELECT tipo, numero, saldo, estado
        FROM productos
        WHERE id_asociado = ?
        ORDER BY tipo, numero
    """
    with obtener_conexion() as conexion:
        return conexion.execute(consulta, (id_asociado,)).fetchall()


def obtener_resumen_financiero(id_asociado):
    """Ahorros y deuda consolidados. COALESCE evita NULL sin productos."""
    consulta = """
        SELECT
            COALESCE(SUM(CASE WHEN tipo = 'AHORRO'  THEN saldo END), 0) AS total_ahorros,
            COALESCE(SUM(CASE WHEN tipo = 'CREDITO' THEN saldo END), 0) AS total_deuda,
            COUNT(*) AS cantidad_productos,
            SUM(CASE WHEN estado = 'MORA' THEN 1 ELSE 0 END) AS productos_en_mora
        FROM productos
        WHERE id_asociado = ?
    """
    with obtener_conexion() as conexion:
        return conexion.execute(consulta, (id_asociado,)).fetchone()


# ------------------------------------------------------------------
# Auditoría
# ------------------------------------------------------------------
def registrar_evento(usuario_intento, evento, id_asociado=None, ip_origen=None):
    """Registra el intento. Nunca recibe ni guarda la contraseña."""
    with obtener_conexion() as conexion:
        conexion.execute(
            """
            INSERT INTO auditoria_accesos
                (id_asociado, usuario_intento, evento, ip_origen)
            VALUES (?, ?, ?, ?)
            """,
            (id_asociado, usuario_intento, evento, ip_origen),
        )


def obtener_ultimos_eventos(id_asociado, limite=5):
    consulta = """
        SELECT evento, ip_origen, fecha_evento
        FROM auditoria_accesos
        WHERE id_asociado = ?
        ORDER BY fecha_evento DESC, id_evento DESC
        LIMIT ?
    """
    with obtener_conexion() as conexion:
        return conexion.execute(consulta, (id_asociado, limite)).fetchall()