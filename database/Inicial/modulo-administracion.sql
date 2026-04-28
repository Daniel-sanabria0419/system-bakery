
-- =====================================================
-- TABLA EVENTOS_SISTEMA — Auditoria global
-- Registra cualquier evento importante del sistema
-- datos_anteriores y datos_nuevos en JSONB para
-- guardar exactamente que cambio sin tablas adicionales
-- =====================================================
 
CREATE TABLE eventos_sistema (
    id               BIGSERIAL PRIMARY KEY,
    tabla_afectada   VARCHAR(60) NOT NULL,
    registro_id      BIGINT NOT NULL,
    tipo_evento      VARCHAR(50) NOT NULL,
    descripcion      TEXT NOT NULL,
    datos_anteriores JSONB,
    datos_nuevos     JSONB,
    usuario_id       BIGINT,
    fecha_creacion   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 
    CONSTRAINT fk_eventos_sistema_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
);
 
CREATE INDEX idx_eventos_sistema_tabla_afectada
ON eventos_sistema(tabla_afectada);
 
CREATE INDEX idx_eventos_sistema_registro_id
ON eventos_sistema(registro_id);
 
CREATE INDEX idx_eventos_sistema_tipo_evento
ON eventos_sistema(tipo_evento);
 
CREATE INDEX idx_eventos_sistema_usuario_id
ON eventos_sistema(usuario_id);
 
CREATE INDEX idx_eventos_sistema_fecha_creacion
ON eventos_sistema(fecha_creacion);
 
-- Indice compuesto para consultar el historial de un registro especifico
CREATE INDEX idx_eventos_sistema_tabla_registro
ON eventos_sistema(tabla_afectada, registro_id, fecha_creacion DESC);
 