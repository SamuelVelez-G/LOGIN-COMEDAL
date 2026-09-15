"""
verificar_datos.py
Script temporal para verificar la capa de acceso a datos.
NO forma parte de la aplicacion final.
"""
import database as db

print("=== 1. Buscar por usuario ===")
a = db.buscar_asociado_por_identificador("arestrepo")
print(a["nombre"], "|", a["correo"], "| estado:", a["estado"])

print("\n=== 2. Buscar por correo (mismo asociado) ===")
b = db.buscar_asociado_por_identificador("ana.restrepo@correo.com")
print(b["nombre"], "-> mismo id:", a["id_asociado"] == b["id_asociado"])

print("\n=== 3. Usuario inexistente ===")
print(db.buscar_asociado_por_identificador("noexiste"))

print("\n=== 4. INTENTO DE INYECCION SQL ===")
ataque = "' OR '1'='1"
r = db.buscar_asociado_por_identificador(ataque)
print(f"Entrada maliciosa: {ataque}")
print("Resultado:", r, "<- la consulta parametrizada lo trata como texto literal")

print("\n=== 5. Resumen financiero ===")
res = db.obtener_resumen_financiero(a["id_asociado"])
print(f"Ahorros: ${res['total_ahorros']:,.0f}")
print(f"Deuda:   ${res['total_deuda']:,.0f}")
print(f"Productos: {res['cantidad_productos']} | En mora: {res['productos_en_mora']}")

print("\n=== 6. Productos ===")
for p in db.obtener_productos(a["id_asociado"]):
    print(f"  {p['tipo']:8} {p['numero']:10} ${p['saldo']:>14,.0f}  {p['estado']}")

print("\n=== 7. Bloqueo tras 5 intentos fallidos ===")
c = db.buscar_asociado_por_identificador("cgomez")
for i in range(1, 6):
    bloqueado = db.registrar_intento_fallido(c["id_asociado"])
    print(f"  Intento {i} -> bloqueado: {bloqueado}")

c = db.buscar_asociado_por_identificador("cgomez")
esta, mins = db.esta_bloqueado(c)
print(f"  Estado: bloqueado={esta}, minutos restantes={mins}")

print("\n=== 8. Auditoria ===")
db.registrar_evento("cgomez", "CUENTA_BLOQUEADA", c["id_asociado"], "127.0.0.1")
db.registrar_evento("arestrepo", "LOGIN_EXITOSO", a["id_asociado"], "127.0.0.1")
for e in db.obtener_ultimos_eventos(c["id_asociado"]):
    print(f"  {e['fecha_evento']} | {e['evento']} | {e['ip_origen']}")

print("\n=== 9. Acceso exitoso reinicia el bloqueo ===")
db.registrar_acceso_exitoso(c["id_asociado"])
c = db.buscar_asociado_por_identificador("cgomez")
print("  bloqueado_hasta:", c["bloqueado_hasta"], "| intentos:", c["intentos_fallidos"])
