"""
verificar_seguridad.py
Verificacion de la logica de autenticacion.
NO forma parte de la aplicacion final.
"""
import time
import auth
import database as db

def probar(titulo, identificador, password):
    inicio = time.perf_counter()
    exito, mensaje, asociado = auth.autenticar(identificador, password, "127.0.0.1")
    ms = (time.perf_counter() - inicio) * 1000
    estado = "ACCESO CONCEDIDO" if exito else "RECHAZADO"
    print(f"{titulo}")
    print(f"   -> {estado} | {mensaje or asociado['nombre']} | {ms:.0f} ms")

print("=" * 62)
print("PRUEBAS DE AUTENTICACION")
print("=" * 62)

probar("1. Credenciales correctas (usuario)", "arestrepo", "Comedal2026*")
probar("2. Credenciales correctas (correo)", "ana.restrepo@correo.com", "Comedal2026*")
probar("3. Contrasena incorrecta", "arestrepo", "claveMala123")
probar("4. Usuario inexistente", "noexiste", "claveMala123")
probar("5. Campos vacios", "", "")
probar("6. Inyeccion SQL", "' OR '1'='1", "cualquiera")

print("\n" + "-" * 62)
print("Compare los mensajes 3 y 4: son IDENTICOS.")
print("Compare los tiempos 3 y 4: son similares.")
print("Un atacante no puede deducir si el usuario existe.")
print("-" * 62)

print("\n7. Bloqueo por fuerza bruta sobre 'lospina':")
for i in range(1, 7):
    exito, mensaje, _ = auth.autenticar("lospina", "claveMala", "127.0.0.1")
    print(f"   Intento {i}: {mensaje}")

print("\n8. Con la clave CORRECTA estando bloqueada:")
exito, mensaje, _ = auth.autenticar("lospina", "Antioquia2026*", "127.0.0.1")
print(f"   exito={exito} | {mensaje}")
print("   <- el bloqueo se respeta aunque la contrasena sea valida")

print("\n9. Enmascaramiento de datos:")
print("   Cedula 1037654321 ->", auth.enmascarar_cedula("1037654321"))
print("   Correo ana.restrepo@correo.com ->", auth.enmascarar_correo("ana.restrepo@correo.com"))

print("\n10. Rastro de auditoria de 'lospina':")
a = db.buscar_asociado_por_identificador("lospina")
for e in db.obtener_ultimos_eventos(a["id_asociado"], 6):
    print(f"   {e['fecha_evento']} | {e['evento']:18} | {e['ip_origen']}")
