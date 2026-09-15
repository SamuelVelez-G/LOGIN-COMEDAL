"""
Crea la base de datos y carga datos de prueba.  Uso: python init_db.py

Las contraseñas se guardan como hash con salt (scrypt), nunca en texto plano.
"""

import os
import sqlite3

from werkzeug.security import generate_password_hash

RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(RUTA_BASE, "comedal.db")
RUTA_SCHEMA = os.path.join(RUTA_BASE, "schema.sql")


# Datos ficticios. La contraseña en claro solo existe aquí para generar
# el hash y documentar las credenciales de evaluación.
ASOCIADOS_DEMO = [
    {
        "cedula": "1037654321",
        "nombre": "Ana María Restrepo",
        "usuario": "arestrepo",
        "correo": "ana.restrepo@correo.com",
        "password": "Comedal2026*",
        "productos": [
            ("AHORRO", "AH-4001", 7_450_000, "VIGENTE"),
            ("CREDITO", "CR-9012", 18_500_000, "VIGENTE"),
        ],
    },
    {
        "cedula": "8123456",
        "nombre": "Carlos Andrés Gómez",
        "usuario": "cgomez",
        "correo": "carlos.gomez@correo.com",
        "password": "Medellin2026*",
        "productos": [
            ("AHORRO", "AH-4002", 1_280_000, "VIGENTE"),
            ("CREDITO", "CR-9013", 4_300_000, "MORA"),
        ],
    },
    {
        "cedula": "43567890",
        "nombre": "Luisa Fernanda Ospina",
        "usuario": "lospina",
        "correo": "luisa.ospina@correo.com",
        "password": "Antioquia2026*",
        "productos": [
            ("AHORRO", "AH-4003", 22_900_000, "VIGENTE"),
        ],
    },
]


def crear_base_de_datos():
    if os.path.exists(RUTA_DB):
        os.remove(RUTA_DB)
        print("Base de datos anterior eliminada.")

    with open(RUTA_SCHEMA, encoding="utf-8") as archivo:
        schema = archivo.read()

    conexion = sqlite3.connect(RUTA_DB)
    conexion.execute("PRAGMA foreign_keys = ON")

    try:
        conexion.executescript(schema)
        print("Esquema creado.")

        for asociado in ASOCIADOS_DEMO:
            cursor = conexion.execute(
                """
                INSERT INTO asociados
                    (cedula, nombre, usuario, correo, password_hash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    asociado["cedula"],
                    asociado["nombre"],
                    asociado["usuario"],
                    asociado["correo"],
                    generate_password_hash(asociado["password"]),
                ),
            )
            id_asociado = cursor.lastrowid

            for tipo, numero, saldo, estado in asociado["productos"]:
                conexion.execute(
                    """
                    INSERT INTO productos
                        (id_asociado, tipo, numero, saldo, estado)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (id_asociado, tipo, numero, saldo, estado),
                )

        conexion.commit()
        print(f"{len(ASOCIADOS_DEMO)} asociados cargados con sus productos.")

    except sqlite3.Error as error:
        conexion.rollback()
        print(f"Error al inicializar la base de datos: {error}")
        raise
    finally:
        conexion.close()


if __name__ == "__main__":
    crear_base_de_datos()
    print(f"\nListo. Base de datos creada en: {RUTA_DB}")
    print("\nCredenciales de prueba:")
    for asociado in ASOCIADOS_DEMO:
        print(f"  {asociado['usuario']:12} / {asociado['password']}")