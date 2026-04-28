
--TABLA RECETAS
CREATE TABLE recetas(
id BIGSERIAL PRIMARY KEY,
nombre_receta VARCHAR(100) UNIQUE NOT NULL,
producto_resultado_id BIGINT NOT NULL,
descripcion TEXT ,
cantidad_resultado NUMERIC(12,2) NOT NULL,
unidad_medida_resultado_id BIGINT NOT NULL,
activo BOOLEAN NOT NULL DEFAULT TRUE,
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,


CONSTRAINT fk_recetas_producto_resultado
FOREIGN KEY (producto_resultado_id)
REFERENCES productos(id),

CONSTRAINT fk_recetas_unidad_medida_resultado
FOREIGN KEY (unidad_medida_resultado_id)
REFERENCES unidades_medida(id),

CONSTRAINT chk_recetas_cantidad_resultado CHECK (cantidad_resultado > 0)


);


--TABLA DETALLES DE RECETAS
CREATE TABLE detalles_receta(
id BIGSERIAL PRIMARY KEY, 
receta_id BIGINT NOT NULL,
producto_insumo_id BIGINT NOT NULL,
cantidad NUMERIC(12,2) NOT NULL, 

CONSTRAINT fk_detalles_receta_receta
FOREIGN KEY (receta_id)
REFERENCES recetas(id),

CONSTRAINT fk_detalles_receta_producto_insumo
FOREIGN KEY (producto_insumo_id)
REFERENCES productos(id),

CONSTRAINT chk_detalles_receta_cantidad CHECK (cantidad > 0)
);


--TABLA DE ESTADOS DE PRODUCCION
CREATE TABLE estados_produccion(
id BIGSERIAL PRIMARY KEY,
nombre VARCHAR (30) UNIQUE NOT NULL,
descripcion TEXT NOT NULL,
activo BOOLEAN NOT NULL DEFAULT TRUE,
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


--TABLA DE LAS PRODUCCIONES
CREATE TABLE producciones(
id BIGSERIAL PRIMARY KEY,
fecha_programada TIMESTAMPTZ NOT NULL,
fecha_inicio TIMESTAMPTZ,
fecha_fin TIMESTAMPTZ,
usuario_id BIGINT NOT NULL,
estado_produccion_id BIGINT NOT NULL,
observaciones TEXT,
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

CONSTRAINT fk_producciones_usuario
FOREIGN KEY (usuario_id)
REFERENCES usuarios(id),

CONSTRAINT fk_producciones_estado
FOREIGN KEY (estado_produccion_id)
REFERENCES estados_produccion(id)
);


-TABLA DE LOS DETALLES DE PRODUCCION
CREATE TABLE detalles_produccion(
id BIGSERIAL PRIMARY KEY,
produccion_id BIGINT NOT NULL,
receta_id BIGINT NOT NULL,
cantidad_esperada NUMERIC(12,2) NOT NULL,
cantidad_real NUMERIC(12,2),

CONSTRAINT fk_detalles_produccion_receta
FOREIGN KEY (receta_id)
REFERENCES recetas(id),

CONSTRAINT fk_detalles_produccion_produccion
FOREIGN KEY (produccion_id)
REFERENCES producciones(id),

CONSTRAINT chk_detalles_produccion_cantidad_esperada CHECK (cantidad_esperada > 0),
CONSTRAINT chk_detalles_produccion_cantidad_real CHECK (cantidad_real >= 0)
);



--TABLA DE LOS PASOS DE LA RECETA
CREATE TABLE pasos_receta(
id BIGSERIAL PRIMARY KEY,
receta_id BIGINT NOT NULL,
orden_paso INT NOT NULL,
titulo VARCHAR(80) NOT NULL,
descripcion TEXT NOT NULL,
temperatura	INT ,
tiempo_minutos INT,
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

CONSTRAINT fk_pasos_receta_receta
FOREIGN KEY (receta_id)
REFERENCES recetas(id),

CONSTRAINT uq_pasos_receta_orden UNIQUE (receta_id, orden_paso),

CONSTRAINT chk_pasos_receta_orden CHECK (orden_paso > 0),
CONSTRAINT chk_pasos_receta_tiempo CHECK (tiempo_minutos >= 0),
CONSTRAINT chk_pasos_receta_temperatura CHECK (temperatura >= 0)
);


-- =====================================================
-- INDICES TABLA RECETAS
-- =====================================================

CREATE INDEX idx_recetas_producto_resultado_id
ON recetas(producto_resultado_id);

CREATE INDEX idx_recetas_unidad_medida_resultado_id
ON recetas(unidad_medida_resultado_id);

CREATE INDEX idx_recetas_activo
ON recetas(activo);



-- =====================================================
-- INDICES TABLA DETALLES_RECETA
-- =====================================================

CREATE INDEX idx_detalles_receta_receta_id
ON detalles_receta(receta_id);

CREATE INDEX idx_detalles_receta_producto_insumo_id
ON detalles_receta(producto_insumo_id);



-- =====================================================
-- INDICES TABLA ESTADOS_PRODUCCION
-- =====================================================

CREATE INDEX idx_estados_produccion_activo
ON estados_produccion(activo);



-- =====================================================
-- INDICES TABLA PRODUCCIONES
-- =====================================================

CREATE INDEX idx_producciones_fecha_programada
ON producciones(fecha_programada);

CREATE INDEX idx_producciones_fecha_inicio
ON producciones(fecha_inicio);

CREATE INDEX idx_producciones_fecha_fin
ON producciones(fecha_fin);

CREATE INDEX idx_producciones_usuario_id
ON producciones(usuario_id);

CREATE INDEX idx_producciones_estado_produccion_id
ON producciones(estado_produccion_id);



-- =====================================================
-- INDICES TABLA DETALLES_PRODUCCION
-- =====================================================

CREATE INDEX idx_detalles_produccion_produccion_id
ON detalles_produccion(produccion_id);

CREATE INDEX idx_detalles_produccion_receta_id
ON detalles_produccion(receta_id);



-- =====================================================
-- INDICES TABLA PASOS_RECETA
-- =====================================================

CREATE INDEX idx_pasos_receta_receta_id
ON pasos_receta(receta_id);

CREATE INDEX idx_pasos_receta_orden_paso
ON pasos_receta(orden_paso);

CREATE INDEX idx_pasos_receta_receta_orden
ON pasos_receta(receta_id, orden_paso);