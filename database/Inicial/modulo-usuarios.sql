--Creacion de tabla empleados
CREATE TABLE empleados (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL,
    apellido VARCHAR(80) NOT NULL,
    documento VARCHAR(30) UNIQUE NOT NULL,
    celular VARCHAR(20),
    direccion VARCHAR(150),
    cargo VARCHAR(80),
    email VARCHAR(120) UNIQUE,
    fecha_ingreso DATE NOT NULL,
    fecha_retiro DATE,
    salario NUMERIC(12,2),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
--indices de la tabla empleados
CREATE INDEX idx_empleados_nombre ON empleados(nombre);

--Creacion de tabla roles para los usuarios
CREATE TABLE roles (
    id SMALLSERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

--Creacion de tabla estados para los usuarios
CREATE TABLE estados_usuarios (
    id SMALLSERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

--Creacion de tabla usuarios
CREATE TABLE usuarios (
    id BIGSERIAL PRIMARY KEY,
    empleado_id BIGINT NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol_id BIGINT NOT NULL,
    email VARCHAR(120) UNIQUE,
    ultimo_login TIMESTAMP,
    estado_id BIGINT NOT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

        --Forgenkey de la tabla usuarios
    CONSTRAINT fk_usuario_empleado
        FOREIGN KEY (empleado_id)
        REFERENCES empleados(id),

    CONSTRAINT fk_usuario_rol
        FOREIGN KEY (rol_id)
        REFERENCES roles(id),

    CONSTRAINT fk_usuario_estado
        FOREIGN KEY (estado_id)
        REFERENCES estados_usuarios(id)
);


--Indices de la tabla usuarios
CREATE INDEX idx_usuarios_empleado_id ON usuarios(empleado_id);
CREATE INDEX idx_usuarios_rol_id ON usuarios(rol_id);
CREATE INDEX idx_usuarios_estado_id ON usuarios(estado_id);

