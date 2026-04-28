--Creacion tabla tipos de venta para ventas
CREATE TABLE tipos_venta (
id BIGSERIAL PRIMARY KEY,
nombre VARCHAR(50) UNIQUE NOT NULL,
descripcion TEXT,
activo BOOLEAN NOT NULL DEFAULT TRUE,
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

--Creacion tabla tipos de descuento para ventas
CREATE TABLE tipos_descuento (
id BIGSERIAL PRIMARY KEY,
nombre VARCHAR(50) UNIQUE NOT NULL,
descripcion TEXT,
valor_descuento NUMERIC(12,2) NOT NULL,
activo BOOLEAN NOT NULL DEFAULT TRUE,
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
/*posibles proximos campos
modo_descuento
*/
);

--Creacion tabla metodos de pago para ventas
CREATE TABLE metodos_pago (
id BIGSERIAL PRIMARY KEY,
nombre VARCHAR(50) UNIQUE NOT NULL,
descripcion TEXT,
activo BOOLEAN NOT NULL DEFAULT TRUE,
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE cajas(
id BIGSERIAL PRIMARY KEY,
fecha_apertura TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, --fecha y hora en la que se abre la caja
fecha_cierre TIMESTAMPTZ, -- fecha y hora en la que se cierra la caja
usuario_apertura_id BIGINT NOT NULL,  --usuario quien abre la caja
usuario_cierre_id BIGINT,  --usuario quien cierra la caja
efectivo_inicial NUMERIC(12,2) NOT NULL, --efectivo inicial que hay en caja
efectivo_esperado NUMERIC(12,2), --efectivo esperado al cierrre de la caja
efectivo_obtenido NUMERIC(12,2),  --efectivo que se obtiene al cierre de la caja
diferencia NUMERIC(12,2), 		--diferencia entre el efectivo esperado y el obtenido
estado VARCHAR(20) NOT NULL DEFAULT 'ABIERTA',
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, --fecha de creacion del registro

    CONSTRAINT chk_caja_estado CHECK (estado IN ('ABIERTA','CERRADA','ANULADA')),

 CONSTRAINT fk_caja_usuario_apertura

        FOREIGN KEY (usuario_apertura_id)

        REFERENCES usuarios(id),

    CONSTRAINT fk_caja_usuario_cierre

        FOREIGN KEY (usuario_cierre_id)

        REFERENCES usuarios(id)
);


CREATE INDEX idx_cajas_usuario_apertura

ON cajas(usuario_apertura_id);

CREATE INDEX idx_cajas_usuario_cierre

ON cajas(usuario_cierre_id);

CREATE INDEX idx_cajas_estado

ON cajas(estado);








--Creacion de tabla de ventas
CREATE TABLE ventas (
id BIGSERIAL PRIMARY KEY,
fecha TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, --fecha y hora en la que se registro la compra
usuario_id BIGINT NOT NULL, --usuarios que registro la compra
caja_id BIGINT NOT NULL,
metodo_pago_id BIGINT NOT NULL, --nequi, brebe, daviplata, efectivo otro 
tipo_venta_id BIGINT NOT NULL, --En caja, Pedido, domicilio, otro
subtotal NUMERIC(12,2) NOT NULL, --total antes del descuento 
descuento NUMERIC(12,2) NOT NULL DEFAULT 0,
total NUMERIC(12,2) NOT NULL, --total de la compra (saldo a cobrar)
efectivo_recibido NUMERIC(12,2), --dinero recibido por el cajero 
cambio NUMERIC(12,2), --cambio devuelto por el cajero
observaciones varchar(200), --Algunos comentarios acerca de la compra 
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, --Fecha en la que se crea el registro




   CONSTRAINT chk_ventas_subtotal CHECK (subtotal >= 0),

    CONSTRAINT chk_ventas_descuento CHECK (descuento >= 0),

    CONSTRAINT chk_ventas_total CHECK (total >= 0),
	
    CONSTRAINT fk_ventas_usuario

        FOREIGN KEY (usuario_id)

        REFERENCES usuarios(id),

    CONSTRAINT fk_ventas_metodo_pago

        FOREIGN KEY (metodo_pago_id)

        REFERENCES metodos_pago(id),

    CONSTRAINT fk_ventas_tipo_venta

        FOREIGN KEY (tipo_venta_id)

        REFERENCES tipos_venta(id),
		
		CONSTRAINT fk_ventas_caja

        FOREIGN KEY (caja_id)

        REFERENCES cajas(id)

);


CREATE INDEX idx_ventas_fecha

ON ventas(fecha);

CREATE INDEX idx_ventas_usuario_id

ON ventas(usuario_id);

CREATE INDEX idx_ventas_tipo_venta_id

ON ventas(tipo_venta_id);

CREATE INDEX idx_ventas_caja_id ON ventas(caja_id);
CREATE INDEX idx_ventas_metodo_pago_id ON ventas(metodo_pago_id);


CREATE TABLE detalles_venta(
id BIGSERIAL PRIMARY KEY,
venta_id BIGINT NOT NULL, --venta general 
producto_id BIGINT NOT NULL, --producto de la venta
cantidad NUMERIC(12,2) NOT NULL, --cantidad del producto
precio_unitario NUMERIC(12,2) NOT NULL, --precio unitario del producto
subtotal NUMERIC(12,2) NOT NULL, 	--subtotal antes del descuento 
descuento NUMERIC(12,2) NOT NULL DEFAULT 0,	--cantidad del descuento
tipo_descuento_id BIGINT NOT NULL, --si aplica algun descuento 7x2000 u otro 
total NUMERIC(12,2) NOT NULL,	--total despues del descuento
fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, --fecha de creacion de la venta

CONSTRAINT chk_detalle_cantidad CHECK (cantidad > 0),
CONSTRAINT chk_detalle_precio CHECK (precio_unitario >= 0),
CONSTRAINT chk_detalle_total CHECK (total >= 0),

CONSTRAINT fk_detalle_venta_venta

        FOREIGN KEY (venta_id)

        REFERENCES ventas(id),

  CONSTRAINT fk_detalle_venta_producto

        FOREIGN KEY (producto_id)

        REFERENCES productos(id),
		
CONSTRAINT fk_detalle_venta_tipo_descuento

        FOREIGN KEY (tipo_descuento_id)

        REFERENCES tipos_descuento(id)
);

CREATE INDEX idx_detalles_venta_producto_id
ON detalles_venta(producto_id);

CREATE INDEX idx_detalles_venta_fecha_creacion
ON detalles_venta(fecha_creacion);

CREATE INDEX idx_detalles_venta_tipo_descuento_id
ON detalles_venta(tipo_descuento_id);

CREATE INDEX idx_detalles_venta_venta_id
ON detalles_venta(venta_id);



CREATE TABLE tipos_movimiento_caja (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    naturaleza VARCHAR(10) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
	 CONSTRAINT chk_tipos_movimiento_caja_naturaleza CHECK (naturaleza IN ('ENTRADA','SALIDA'))
);




CREATE TABLE movimientos_caja (
    id BIGSERIAL PRIMARY KEY,
    caja_id BIGINT NOT NULL,
    usuario_id BIGINT NOT NULL,
    tipo_movimiento_id BIGINT NOT NULL,
    valor NUMERIC(12,2) NOT NULL,
    observacion TEXT NOT NULL,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

CONSTRAINT chk_movimientos_valor CHECK (valor > 0),

    CONSTRAINT fk_mov_caja

        FOREIGN KEY (caja_id)

        REFERENCES cajas(id),

    CONSTRAINT fk_mov_usuario

        FOREIGN KEY (usuario_id)

        REFERENCES usuarios(id),

    CONSTRAINT fk_mov_tipo

        FOREIGN KEY (tipo_movimiento_id)

        REFERENCES tipos_movimiento_caja(id)

);

CREATE INDEX idx_movimientos_caja_caja_id
ON movimientos_caja(caja_id);

CREATE INDEX idx_movimientos_caja_usuario_id
ON movimientos_caja(usuario_id);

CREATE INDEX idx_movimientos_caja_tipo_movimiento_id
ON movimientos_caja(tipo_movimiento_id);

CREATE INDEX idx_movimientos_caja_fecha
ON movimientos_caja(fecha_creacion);
