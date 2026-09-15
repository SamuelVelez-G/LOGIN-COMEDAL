-- Esquema de la base de datos.  Motor: SQLite 3.
-- Las llaves foráneas se habilitan en la conexión con PRAGMA foreign_keys = ON.

DROP TABLE IF EXISTS auditoria_accesos;
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS asociados;

-- Asociados. No se guarda la contraseña, sino su hash con salt.
CREATE TABLE asociados (
    id_asociado        INTEGER PRIMARY KEY AUTOINCREMENT,
    cedula             TEXT NOT NULL UNIQUE,
    nombre             TEXT NOT NULL,
    usuario            TEXT NOT NULL UNIQUE,
    correo             TEXT NOT NULL UNIQUE,
    password_hash      TEXT NOT NULL,
    estado             TEXT NOT NULL DEFAULT 'ACTIVO'
                            CHECK (estado IN ('ACTIVO','INACTIVO','BLOQUEADO')),
    intentos_fallidos  INTEGER NOT NULL DEFAULT 0,
    bloqueado_hasta    TEXT,
    ultimo_acceso      TEXT,
    fecha_creacion     TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Índices sobre las columnas usadas al iniciar sesión.
CREATE INDEX idx_asociados_usuario ON asociados (usuario);
CREATE INDEX idx_asociados_correo  ON asociados (correo);

-- Productos del asociado (1:N). Alimentan la sección privada.
CREATE TABLE productos (
    id_producto   INTEGER PRIMARY KEY AUTOINCREMENT,
    id_asociado   INTEGER NOT NULL,
    tipo          TEXT NOT NULL CHECK (tipo IN ('AHORRO','CREDITO')),
    numero        TEXT NOT NULL UNIQUE,
    saldo         REAL NOT NULL DEFAULT 0,
    estado        TEXT NOT NULL DEFAULT 'VIGENTE'
                       CHECK (estado IN ('VIGENTE','CANCELADO','MORA')),
    FOREIGN KEY (id_asociado)
        REFERENCES asociados (id_asociado)
        ON DELETE CASCADE
);

CREATE INDEX idx_productos_asociado ON productos (id_asociado);

-- Auditoría de accesos. Guarda el identificador intentado,
-- nunca la contraseña.
CREATE TABLE auditoria_accesos (
    id_evento       INTEGER PRIMARY KEY AUTOINCREMENT,
    id_asociado     INTEGER,
    usuario_intento TEXT NOT NULL,
    evento          TEXT NOT NULL
                         CHECK (evento IN ('LOGIN_EXITOSO',
                                           'LOGIN_FALLIDO',
                                           'CUENTA_BLOQUEADA',
                                           'LOGOUT',
                                           'SESION_EXPIRADA')),
    ip_origen       TEXT,
    fecha_evento    TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (id_asociado)
        REFERENCES asociados (id_asociado)
        ON DELETE SET NULL
);

CREATE INDEX idx_auditoria_fecha ON auditoria_accesos (fecha_evento);