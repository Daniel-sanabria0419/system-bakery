CREATE TABLE tipos_producto(
id BIGSERIAL PRIMARY KEY,
nombre VARCHAR(50) UNIQUE NOT NULL,
descripcion VARCHAR(100),
activo BOOLEAN NOT NULL DEFAULT TRUE,
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categorias_producto(
id BIGSERIAL PRIMARY KEY,
nombre VARCHAR(40) UNIQUE NOT NULL,
descripcion VARCHAR(100),
activo BOOLEAN NOT NULL DEFAULT TRUE,
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE unidades_medida(
id BIGSERIAL PRIMARY KEY,
nombre VARCHAR(20) UNIQUE NOT NULL,
descripcion VARCHAR(100),
activo BOOLEAN NOT NULL DEFAULT TRUE,
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE productos(
id BIGSERIAL PRIMARY KEY,
categoria_id BIGINT NOT NULL,
tipo_producto_id BIGINT NOT NULL,
nombre VARCHAR(100) UNIQUE NOT NULL,
descripcion VARCHAR(200),
codigo_barras TEXT UNIQUE,
costo NUMERIC(12,2) NOT NULL,
precio_venta NUMERIC(12,2),
unidad_medida_id BIGINT NOT NULL,
activo BOOLEAN NOT NULL DEFAULT TRUE,
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

CONSTRAINT chk_productos_costo CHECK (costo >= 0),
CONSTRAINT chk_productos_precio_venta CHECK (precio_venta >= 0),
CONSTRAINT fk_producto_categoria FOREIGN KEY (categoria_id) REFERENCES categorias_producto(id),
CONSTRAINT fk_producto_tipo_producto FOREIGN KEY (tipo_producto_id) REFERENCES tipos_producto(id),
CONSTRAINT fk_producto_unidad_medida FOREIGN KEY (unidad_medida_id) REFERENCES unidades_medida(id)



);


CREATE TABLE stock_producto(
id BIGSERIAL PRIMARY KEY,
producto_id BIGINT UNIQUE NOT NULL,
cantidad_actual NUMERIC(12,2) NOT NULL,
fecha_ultima_actualizacion TIMESTAMPTZ,
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

CONSTRAINT chk_stock_producto_cantidad_actual CHECK (cantidad_actual >= 0),
CONSTRAINT fk_stock_producto_producto FOREIGN KEY (producto_id) REFERENCES productos(id)
);


CREATE TABLE tipos_movimiento_stock(
id BIGSERIAL PRIMARY KEY,
nombre VARCHAR(50) UNIQUE NOT NULL,
descripcion VARCHAR(150) NOT NULL,
naturaleza VARCHAR(50) NOT NULL,
activo BOOLEAN NOT NULL DEFAULT TRUE,
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

CONSTRAINT chk_tipos_movimiento_stock_naturaleza CHECK (naturaleza IN ('ENTRADA','SALIDA','AJUSTE'))
);

CREATE TABLE movimientos_stock_producto(
id BIGSERIAL PRIMARY KEY,
producto_id BIGINT NOT NULL,
tipo_movimiento_id BIGINT NOT NULL,
cantidad NUMERIC(12,2) NOT NULL,
stock_anterior NUMERIC(12,2) NOT NULL,
stock_actual NUMERIC(12,2) NOT NULL,
observaciones VARCHAR(200),
usuario_id BIGINT NOT NULL,
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,


CONSTRAINT chk_movimientos_stock_producto_stock_anterior CHECK (stock_anterior >= 0),
CONSTRAINT chk_movimientos_stock_producto_cantidad CHECK (cantidad > 0),
CONSTRAINT chk_movimientos_stock_producto_stock_actual CHECK (stock_actual >= 0),
CONSTRAINT fk_movimientos_stock_producto_producto FOREIGN KEY (producto_id) REFERENCES productos(id),
CONSTRAINT fk_movimientos_stock_producto_tipo_movimiento FOREIGN KEY (tipo_movimiento_id) REFERENCES tipos_movimiento_stock(id),
CONSTRAINT fk_movimientos_stock_producto_usuarios FOREIGN KEY (usuario_id) REFERENCES usuarios(id)


);

--Indices de productos

CREATE INDEX idx_productos_nombre
ON productos(nombre);

CREATE INDEX idx_productos_categoria_id
ON productos(categoria_id);

CREATE INDEX idx_productos_tipo_producto_id
ON productos(tipo_producto_id);

CREATE INDEX idx_productos_unidad_medida_id
ON productos(unidad_medida_id);

CREATE INDEX idx_productos_activo
ON productos(activo);

--Indices de stock_prodcuto
CREATE INDEX idx_stock_producto_producto_id
ON stock_producto(producto_id);

CREATE INDEX idx_stock_producto_fecha_actualizacion
ON stock_producto(fecha_ultima_actualizacion);

--Indices de movimineto_stock_producto


CREATE INDEX idx_mov_stock_producto_id
ON movimientos_stock_producto(producto_id);

CREATE INDEX idx_mov_stock_tipo_movimiento_id
ON movimientos_stock_producto(tipo_movimiento_id);

CREATE INDEX idx_mov_stock_usuario_id
ON movimientos_stock_producto(usuario_id);

CREATE INDEX idx_mov_stock_fecha
ON movimientos_stock_producto(fecha_creacion);