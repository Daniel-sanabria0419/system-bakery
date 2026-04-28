--
-- PostgreSQL database dump
--

\restrict Ugwku8nRxetd7qatMLmYtzAFHLyqhVCqlZVslJ6q3HcUgAhho16Ly8Dnejb0gYf

-- Dumped from database version 18.3 (Homebrew)
-- Dumped by pg_dump version 18.2

-- Started on 2026-04-24 20:17:06 -05

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 234 (class 1259 OID 16538)
-- Name: cajas; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.cajas (
    id bigint NOT NULL,
    fecha_apertura timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_cierre timestamp with time zone,
    usuario_apertura_id bigint NOT NULL,
    usuario_cierre_id bigint,
    efectivo_inicial numeric(12,2) NOT NULL,
    efectivo_esperado numeric(12,2),
    efectivo_obtenido numeric(12,2),
    diferencia numeric(12,2),
    estado character varying(20) DEFAULT 'ABIERTA'::character varying NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_caja_estado CHECK (((estado)::text = ANY ((ARRAY['ABIERTA'::character varying, 'CERRADA'::character varying, 'ANULADA'::character varying])::text[])))
);


ALTER TABLE public.cajas OWNER TO daniel;

--
-- TOC entry 233 (class 1259 OID 16537)
-- Name: cajas_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.cajas_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cajas_id_seq OWNER TO daniel;

--
-- TOC entry 4170 (class 0 OID 0)
-- Dependencies: 233
-- Name: cajas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.cajas_id_seq OWNED BY public.cajas.id;


--
-- TOC entry 246 (class 1259 OID 16722)
-- Name: categorias_producto; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.categorias_producto (
    id bigint NOT NULL,
    nombre character varying(40) NOT NULL,
    descripcion character varying(100),
    activo boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.categorias_producto OWNER TO daniel;

--
-- TOC entry 245 (class 1259 OID 16721)
-- Name: categorias_producto_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.categorias_producto_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categorias_producto_id_seq OWNER TO daniel;

--
-- TOC entry 4171 (class 0 OID 0)
-- Dependencies: 245
-- Name: categorias_producto_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.categorias_producto_id_seq OWNED BY public.categorias_producto.id;


--
-- TOC entry 238 (class 1259 OID 16616)
-- Name: detalles_venta; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.detalles_venta (
    id bigint NOT NULL,
    venta_id bigint NOT NULL,
    producto_id bigint NOT NULL,
    cantidad numeric(12,2) NOT NULL,
    precio_unitario numeric(12,2) NOT NULL,
    subtotal numeric(12,2) NOT NULL,
    descuento numeric(12,2) DEFAULT 0 NOT NULL,
    tipo_descuento_id bigint NOT NULL,
    total numeric(12,2) NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_detalle_cantidad CHECK ((cantidad > (0)::numeric)),
    CONSTRAINT chk_detalle_precio CHECK ((precio_unitario >= (0)::numeric)),
    CONSTRAINT chk_detalle_total CHECK ((total >= (0)::numeric))
);


ALTER TABLE public.detalles_venta OWNER TO daniel;

--
-- TOC entry 237 (class 1259 OID 16615)
-- Name: detalles_venta_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.detalles_venta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.detalles_venta_id_seq OWNER TO daniel;

--
-- TOC entry 4172 (class 0 OID 0)
-- Dependencies: 237
-- Name: detalles_venta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.detalles_venta_id_seq OWNED BY public.detalles_venta.id;


--
-- TOC entry 224 (class 1259 OID 16424)
-- Name: empleados; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.empleados (
    id bigint NOT NULL,
    nombre character varying(80) NOT NULL,
    apellido character varying(80) NOT NULL,
    documento character varying(30) NOT NULL,
    celular character varying(20),
    direccion character varying(150),
    cargo character varying(80),
    email character varying(120),
    fecha_ingreso date NOT NULL,
    fecha_retiro date,
    salario numeric(12,2),
    activo boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.empleados OWNER TO daniel;

--
-- TOC entry 223 (class 1259 OID 16423)
-- Name: empleados_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.empleados_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.empleados_id_seq OWNER TO daniel;

--
-- TOC entry 4173 (class 0 OID 0)
-- Dependencies: 223
-- Name: empleados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.empleados_id_seq OWNED BY public.empleados.id;


--
-- TOC entry 222 (class 1259 OID 16407)
-- Name: estados_usuarios; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.estados_usuarios (
    id smallint CONSTRAINT estado_usuarios_id_not_null NOT NULL,
    nombre character varying(50) CONSTRAINT estado_usuarios_nombre_not_null NOT NULL,
    descripcion text,
    activo boolean DEFAULT true CONSTRAINT estado_usuarios_activo_not_null NOT NULL,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP CONSTRAINT estado_usuarios_fecha_creacion_not_null NOT NULL
);


ALTER TABLE public.estados_usuarios OWNER TO daniel;

--
-- TOC entry 221 (class 1259 OID 16406)
-- Name: estado_usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.estado_usuarios_id_seq
    AS smallint
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.estado_usuarios_id_seq OWNER TO daniel;

--
-- TOC entry 4174 (class 0 OID 0)
-- Dependencies: 221
-- Name: estado_usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.estado_usuarios_id_seq OWNED BY public.estados_usuarios.id;


--
-- TOC entry 232 (class 1259 OID 16521)
-- Name: metodos_pago; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.metodos_pago (
    id bigint NOT NULL,
    nombre character varying(50) NOT NULL,
    descripcion text,
    activo boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.metodos_pago OWNER TO daniel;

--
-- TOC entry 231 (class 1259 OID 16520)
-- Name: metodos_pago_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.metodos_pago_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.metodos_pago_id_seq OWNER TO daniel;

--
-- TOC entry 4175 (class 0 OID 0)
-- Dependencies: 231
-- Name: metodos_pago_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.metodos_pago_id_seq OWNED BY public.metodos_pago.id;


--
-- TOC entry 242 (class 1259 OID 16669)
-- Name: movimientos_caja; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.movimientos_caja (
    id bigint NOT NULL,
    caja_id bigint NOT NULL,
    usuario_id bigint NOT NULL,
    tipo_movimiento_id bigint NOT NULL,
    valor numeric(12,2) NOT NULL,
    observacion text NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_movimientos_valor CHECK ((valor > (0)::numeric))
);


ALTER TABLE public.movimientos_caja OWNER TO daniel;

--
-- TOC entry 241 (class 1259 OID 16668)
-- Name: movimientos_caja_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.movimientos_caja_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.movimientos_caja_id_seq OWNER TO daniel;

--
-- TOC entry 4176 (class 0 OID 0)
-- Dependencies: 241
-- Name: movimientos_caja_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.movimientos_caja_id_seq OWNED BY public.movimientos_caja.id;


--
-- TOC entry 256 (class 1259 OID 16830)
-- Name: movimientos_stock_producto; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.movimientos_stock_producto (
    id bigint NOT NULL,
    producto_id bigint NOT NULL,
    tipo_movimiento_id bigint NOT NULL,
    cantidad numeric(12,2) NOT NULL,
    stock_anterior numeric(12,2) NOT NULL,
    stock_actual numeric(12,2) NOT NULL,
    observaciones character varying(200),
    usuario_id bigint NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_movimientos_stock_producto_cantidad CHECK ((cantidad > (0)::numeric)),
    CONSTRAINT chk_movimientos_stock_producto_stock_actual CHECK ((stock_actual >= (0)::numeric)),
    CONSTRAINT chk_movimientos_stock_producto_stock_anterior CHECK ((stock_anterior >= (0)::numeric))
);


ALTER TABLE public.movimientos_stock_producto OWNER TO daniel;

--
-- TOC entry 255 (class 1259 OID 16829)
-- Name: movimientos_stock_producto_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.movimientos_stock_producto_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.movimientos_stock_producto_id_seq OWNER TO daniel;

--
-- TOC entry 4177 (class 0 OID 0)
-- Dependencies: 255
-- Name: movimientos_stock_producto_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.movimientos_stock_producto_id_seq OWNED BY public.movimientos_stock_producto.id;


--
-- TOC entry 250 (class 1259 OID 16752)
-- Name: productos; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.productos (
    id bigint NOT NULL,
    categoria_id bigint NOT NULL,
    tipo_producto_id bigint NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion character varying(200),
    codigo_barras text,
    costo numeric(12,2) NOT NULL,
    precio_venta numeric(12,2),
    unidad_medida_id bigint NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_productos_costo CHECK ((costo >= (0)::numeric)),
    CONSTRAINT chk_productos_precio_venta CHECK ((precio_venta >= (0)::numeric))
);


ALTER TABLE public.productos OWNER TO daniel;

--
-- TOC entry 249 (class 1259 OID 16751)
-- Name: productos_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.productos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.productos_id_seq OWNER TO daniel;

--
-- TOC entry 4178 (class 0 OID 0)
-- Dependencies: 249
-- Name: productos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.productos_id_seq OWNED BY public.productos.id;


--
-- TOC entry 220 (class 1259 OID 16390)
-- Name: roles; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.roles (
    id smallint NOT NULL,
    nombre character varying(60) NOT NULL,
    descripcion text,
    activo boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.roles OWNER TO daniel;

--
-- TOC entry 219 (class 1259 OID 16389)
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.roles_id_seq
    AS smallint
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roles_id_seq OWNER TO daniel;

--
-- TOC entry 4179 (class 0 OID 0)
-- Dependencies: 219
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- TOC entry 252 (class 1259 OID 16792)
-- Name: stock_producto; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.stock_producto (
    id bigint NOT NULL,
    producto_id bigint NOT NULL,
    cantidad_actual numeric(12,2) NOT NULL,
    fecha_ultima_actualizacion timestamp with time zone,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_stock_producto_cantidad_actual CHECK ((cantidad_actual >= (0)::numeric))
);


ALTER TABLE public.stock_producto OWNER TO daniel;

--
-- TOC entry 251 (class 1259 OID 16791)
-- Name: stock_producto_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.stock_producto_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.stock_producto_id_seq OWNER TO daniel;

--
-- TOC entry 4180 (class 0 OID 0)
-- Dependencies: 251
-- Name: stock_producto_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.stock_producto_id_seq OWNED BY public.stock_producto.id;


--
-- TOC entry 230 (class 1259 OID 16503)
-- Name: tipos_descuento; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.tipos_descuento (
    id bigint NOT NULL,
    nombre character varying(50) NOT NULL,
    descripcion text,
    valor_descuento numeric(12,2) NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.tipos_descuento OWNER TO daniel;

--
-- TOC entry 229 (class 1259 OID 16502)
-- Name: tipos_descuento_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.tipos_descuento_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tipos_descuento_id_seq OWNER TO daniel;

--
-- TOC entry 4181 (class 0 OID 0)
-- Dependencies: 229
-- Name: tipos_descuento_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.tipos_descuento_id_seq OWNED BY public.tipos_descuento.id;


--
-- TOC entry 240 (class 1259 OID 16652)
-- Name: tipos_movimiento_caja; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.tipos_movimiento_caja (
    id bigint NOT NULL,
    nombre character varying(50) NOT NULL,
    naturaleza character varying(10) NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_tipos_movimiento_caja_naturaleza CHECK (((naturaleza)::text = ANY ((ARRAY['ENTRADA'::character varying, 'SALIDA'::character varying])::text[])))
);


ALTER TABLE public.tipos_movimiento_caja OWNER TO daniel;

--
-- TOC entry 239 (class 1259 OID 16651)
-- Name: tipos_movimiento_caja_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.tipos_movimiento_caja_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tipos_movimiento_caja_id_seq OWNER TO daniel;

--
-- TOC entry 4182 (class 0 OID 0)
-- Dependencies: 239
-- Name: tipos_movimiento_caja_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.tipos_movimiento_caja_id_seq OWNED BY public.tipos_movimiento_caja.id;


--
-- TOC entry 254 (class 1259 OID 16812)
-- Name: tipos_movimiento_stock; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.tipos_movimiento_stock (
    id bigint NOT NULL,
    nombre character varying(50) NOT NULL,
    descripcion character varying(150) NOT NULL,
    naturaleza character varying(50) NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_tipos_movimiento_stock_naturaleza CHECK (((naturaleza)::text = ANY ((ARRAY['ENTRADA'::character varying, 'SALIDA'::character varying, 'AJUSTE'::character varying])::text[])))
);


ALTER TABLE public.tipos_movimiento_stock OWNER TO daniel;

--
-- TOC entry 253 (class 1259 OID 16811)
-- Name: tipos_movimiento_stock_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.tipos_movimiento_stock_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tipos_movimiento_stock_id_seq OWNER TO daniel;

--
-- TOC entry 4183 (class 0 OID 0)
-- Dependencies: 253
-- Name: tipos_movimiento_stock_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.tipos_movimiento_stock_id_seq OWNED BY public.tipos_movimiento_stock.id;


--
-- TOC entry 244 (class 1259 OID 16707)
-- Name: tipos_producto; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.tipos_producto (
    id bigint NOT NULL,
    nombre character varying(50) NOT NULL,
    descripcion character varying(100),
    activo boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.tipos_producto OWNER TO daniel;

--
-- TOC entry 243 (class 1259 OID 16706)
-- Name: tipos_producto_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.tipos_producto_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tipos_producto_id_seq OWNER TO daniel;

--
-- TOC entry 4184 (class 0 OID 0)
-- Dependencies: 243
-- Name: tipos_producto_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.tipos_producto_id_seq OWNED BY public.tipos_producto.id;


--
-- TOC entry 228 (class 1259 OID 16486)
-- Name: tipos_venta; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.tipos_venta (
    id bigint NOT NULL,
    nombre character varying(50) NOT NULL,
    descripcion text,
    activo boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.tipos_venta OWNER TO daniel;

--
-- TOC entry 227 (class 1259 OID 16485)
-- Name: tipos_venta_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.tipos_venta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tipos_venta_id_seq OWNER TO daniel;

--
-- TOC entry 4185 (class 0 OID 0)
-- Dependencies: 227
-- Name: tipos_venta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.tipos_venta_id_seq OWNED BY public.tipos_venta.id;


--
-- TOC entry 248 (class 1259 OID 16737)
-- Name: unidades_medida; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.unidades_medida (
    id bigint NOT NULL,
    nombre character varying(20) NOT NULL,
    descripcion character varying(100),
    activo boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.unidades_medida OWNER TO daniel;

--
-- TOC entry 247 (class 1259 OID 16736)
-- Name: unidades_medida_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.unidades_medida_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.unidades_medida_id_seq OWNER TO daniel;

--
-- TOC entry 4186 (class 0 OID 0)
-- Dependencies: 247
-- Name: unidades_medida_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.unidades_medida_id_seq OWNED BY public.unidades_medida.id;


--
-- TOC entry 226 (class 1259 OID 16446)
-- Name: usuarios; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.usuarios (
    id bigint NOT NULL,
    empleado_id bigint NOT NULL,
    username character varying(50) NOT NULL,
    password_hash text NOT NULL,
    rol_id bigint NOT NULL,
    email character varying(120),
    ultimo_login timestamp without time zone,
    estado_id bigint NOT NULL,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.usuarios OWNER TO daniel;

--
-- TOC entry 225 (class 1259 OID 16445)
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.usuarios_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO daniel;

--
-- TOC entry 4187 (class 0 OID 0)
-- Dependencies: 225
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- TOC entry 236 (class 1259 OID 16568)
-- Name: ventas; Type: TABLE; Schema: public; Owner: daniel
--

CREATE TABLE public.ventas (
    id bigint NOT NULL,
    fecha timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    usuario_id bigint NOT NULL,
    caja_id bigint NOT NULL,
    metodo_pago_id bigint NOT NULL,
    tipo_venta_id bigint NOT NULL,
    subtotal numeric(12,2) NOT NULL,
    descuento numeric(12,2) DEFAULT 0 NOT NULL,
    total numeric(12,2) NOT NULL,
    efectivo_recibido numeric(12,2),
    cambio numeric(12,2),
    observaciones character varying(200),
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_ventas_descuento CHECK ((descuento >= (0)::numeric)),
    CONSTRAINT chk_ventas_subtotal CHECK ((subtotal >= (0)::numeric)),
    CONSTRAINT chk_ventas_total CHECK ((total >= (0)::numeric))
);


ALTER TABLE public.ventas OWNER TO daniel;

--
-- TOC entry 235 (class 1259 OID 16567)
-- Name: ventas_id_seq; Type: SEQUENCE; Schema: public; Owner: daniel
--

CREATE SEQUENCE public.ventas_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ventas_id_seq OWNER TO daniel;

--
-- TOC entry 4188 (class 0 OID 0)
-- Dependencies: 235
-- Name: ventas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: daniel
--

ALTER SEQUENCE public.ventas_id_seq OWNED BY public.ventas.id;


--
-- TOC entry 3805 (class 2604 OID 16541)
-- Name: cajas id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.cajas ALTER COLUMN id SET DEFAULT nextval('public.cajas_id_seq'::regclass);


--
-- TOC entry 3824 (class 2604 OID 16725)
-- Name: categorias_producto id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.categorias_producto ALTER COLUMN id SET DEFAULT nextval('public.categorias_producto_id_seq'::regclass);


--
-- TOC entry 3813 (class 2604 OID 16619)
-- Name: detalles_venta id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.detalles_venta ALTER COLUMN id SET DEFAULT nextval('public.detalles_venta_id_seq'::regclass);


--
-- TOC entry 3791 (class 2604 OID 16427)
-- Name: empleados id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.empleados ALTER COLUMN id SET DEFAULT nextval('public.empleados_id_seq'::regclass);


--
-- TOC entry 3788 (class 2604 OID 16410)
-- Name: estados_usuarios id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.estados_usuarios ALTER COLUMN id SET DEFAULT nextval('public.estado_usuarios_id_seq'::regclass);


--
-- TOC entry 3802 (class 2604 OID 16524)
-- Name: metodos_pago id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.metodos_pago ALTER COLUMN id SET DEFAULT nextval('public.metodos_pago_id_seq'::regclass);


--
-- TOC entry 3819 (class 2604 OID 16672)
-- Name: movimientos_caja id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.movimientos_caja ALTER COLUMN id SET DEFAULT nextval('public.movimientos_caja_id_seq'::regclass);


--
-- TOC entry 3838 (class 2604 OID 16833)
-- Name: movimientos_stock_producto id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.movimientos_stock_producto ALTER COLUMN id SET DEFAULT nextval('public.movimientos_stock_producto_id_seq'::regclass);


--
-- TOC entry 3830 (class 2604 OID 16755)
-- Name: productos id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.productos ALTER COLUMN id SET DEFAULT nextval('public.productos_id_seq'::regclass);


--
-- TOC entry 3785 (class 2604 OID 16393)
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- TOC entry 3833 (class 2604 OID 16795)
-- Name: stock_producto id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.stock_producto ALTER COLUMN id SET DEFAULT nextval('public.stock_producto_id_seq'::regclass);


--
-- TOC entry 3799 (class 2604 OID 16506)
-- Name: tipos_descuento id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.tipos_descuento ALTER COLUMN id SET DEFAULT nextval('public.tipos_descuento_id_seq'::regclass);


--
-- TOC entry 3816 (class 2604 OID 16655)
-- Name: tipos_movimiento_caja id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.tipos_movimiento_caja ALTER COLUMN id SET DEFAULT nextval('public.tipos_movimiento_caja_id_seq'::regclass);


--
-- TOC entry 3835 (class 2604 OID 16815)
-- Name: tipos_movimiento_stock id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.tipos_movimiento_stock ALTER COLUMN id SET DEFAULT nextval('public.tipos_movimiento_stock_id_seq'::regclass);


--
-- TOC entry 3821 (class 2604 OID 16710)
-- Name: tipos_producto id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.tipos_producto ALTER COLUMN id SET DEFAULT nextval('public.tipos_producto_id_seq'::regclass);


--
-- TOC entry 3796 (class 2604 OID 16489)
-- Name: tipos_venta id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.tipos_venta ALTER COLUMN id SET DEFAULT nextval('public.tipos_venta_id_seq'::regclass);


--
-- TOC entry 3827 (class 2604 OID 16740)
-- Name: unidades_medida id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.unidades_medida ALTER COLUMN id SET DEFAULT nextval('public.unidades_medida_id_seq'::regclass);


--
-- TOC entry 3794 (class 2604 OID 16449)
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- TOC entry 3809 (class 2604 OID 16571)
-- Name: ventas id; Type: DEFAULT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.ventas ALTER COLUMN id SET DEFAULT nextval('public.ventas_id_seq'::regclass);


--
-- TOC entry 4142 (class 0 OID 16538)
-- Dependencies: 234
-- Data for Name: cajas; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.cajas (id, fecha_apertura, fecha_cierre, usuario_apertura_id, usuario_cierre_id, efectivo_inicial, efectivo_esperado, efectivo_obtenido, diferencia, estado, fecha_creacion) FROM stdin;
\.


--
-- TOC entry 4154 (class 0 OID 16722)
-- Dependencies: 246
-- Data for Name: categorias_producto; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.categorias_producto (id, nombre, descripcion, activo, fecha_creacion) FROM stdin;
\.


--
-- TOC entry 4146 (class 0 OID 16616)
-- Dependencies: 238
-- Data for Name: detalles_venta; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.detalles_venta (id, venta_id, producto_id, cantidad, precio_unitario, subtotal, descuento, tipo_descuento_id, total, fecha_creacion) FROM stdin;
\.


--
-- TOC entry 4132 (class 0 OID 16424)
-- Dependencies: 224
-- Data for Name: empleados; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.empleados (id, nombre, apellido, documento, celular, direccion, cargo, email, fecha_ingreso, fecha_retiro, salario, activo, fecha_creacion) FROM stdin;
9	Monica Rocio	Molina Garzon	53070756	3115513924	cll 137 #91-97	Hija del jefe	monicarmolinag@hotmail.com	2015-10-10	\N	2000000.00	t	2026-04-23 13:10:09.641515
10	Richard Alexander	Rios	000000001	000000001	cll 000 #00-00	Pastelero	richard@hotmail.com	2015-10-10	\N	4000000.00	t	2026-04-23 13:10:09.641515
11	Gloria Maria	Figueroa	000000002	000000002	cll 000 #00-00	Tendera	gloria@hotmail.com	2015-10-10	\N	2000000.00	t	2026-04-23 13:10:09.641515
12	Josefina	Reyes	000000003	000000003	cll 000 #00-00	Tendera	josefina@hotmail.com	2015-10-10	\N	2000000.00	t	2026-04-23 13:10:09.641515
13	Alexys Maria	Figueroa	000000004	000000004	cll 000 #00-00	Hornero	alexys@hotmail.com	2015-10-10	\N	2000000.00	t	2026-04-23 13:10:09.641515
14	Geraldine	Gonzales	000000008	000000005	cll 000 #00-00	Tendera	Geraldine@hotmail.com	2015-10-10	\N	1000000.00	t	2026-04-23 13:10:09.641515
15	Maria	Molina	000000005	000000006	cll 000 #00-00	Tendera	Maria@hotmail.com	2015-10-10	\N	2000000.00	t	2026-04-23 13:10:09.641515
16	Luis Alexander	Maracaibo	000000006	000000007	cll 000 #00-00	Panadero	luis@hotmail.com	2015-10-10	\N	2000000.00	t	2026-04-23 13:10:09.641515
17	Hernan	Nuevo	000000007	000000008	cll 000 #00-00	Panadero	hernan@hotmail.com	2015-10-10	\N	2000000.00	t	2026-04-23 13:10:09.641515
1	Daniel Felipe	Sanabria Molina	1031644413	3003917275	cll 137 #91-97	Nieto del jefe	danielsanabria19@outlook.com	2015-10-10	\N	10000000.00	t	2026-04-23 13:02:51.344925
\.


--
-- TOC entry 4130 (class 0 OID 16407)
-- Dependencies: 222
-- Data for Name: estados_usuarios; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.estados_usuarios (id, nombre, descripcion, activo, fecha_creacion) FROM stdin;
1	activo	\N	t	2026-04-23 14:56:44.870392
2	desactivado	\N	t	2026-04-23 14:56:44.870392
3	bloqueado	\N	t	2026-04-23 14:56:44.870392
\.


--
-- TOC entry 4140 (class 0 OID 16521)
-- Dependencies: 232
-- Data for Name: metodos_pago; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.metodos_pago (id, nombre, descripcion, activo, fecha_creacion) FROM stdin;
\.


--
-- TOC entry 4150 (class 0 OID 16669)
-- Dependencies: 242
-- Data for Name: movimientos_caja; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.movimientos_caja (id, caja_id, usuario_id, tipo_movimiento_id, valor, observacion, fecha_creacion) FROM stdin;
\.


--
-- TOC entry 4164 (class 0 OID 16830)
-- Dependencies: 256
-- Data for Name: movimientos_stock_producto; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.movimientos_stock_producto (id, producto_id, tipo_movimiento_id, cantidad, stock_anterior, stock_actual, observaciones, usuario_id, fecha_creacion) FROM stdin;
\.


--
-- TOC entry 4158 (class 0 OID 16752)
-- Dependencies: 250
-- Data for Name: productos; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.productos (id, categoria_id, tipo_producto_id, nombre, descripcion, codigo_barras, costo, precio_venta, unidad_medida_id, activo, fecha_creacion) FROM stdin;
\.


--
-- TOC entry 4128 (class 0 OID 16390)
-- Dependencies: 220
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.roles (id, nombre, descripcion, activo, fecha_creacion) FROM stdin;
1	Gerencial	Acceso en todo el aplicativo	t	2026-04-23 14:50:29.391618
2	Caja	Acceso solo al modulo de cobro	t	2026-04-23 14:50:29.391618
3	Panadero	Acceso solo al modulo de produccion	t	2026-04-23 14:50:29.391618
\.


--
-- TOC entry 4160 (class 0 OID 16792)
-- Dependencies: 252
-- Data for Name: stock_producto; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.stock_producto (id, producto_id, cantidad_actual, fecha_ultima_actualizacion, fecha_creacion) FROM stdin;
\.


--
-- TOC entry 4138 (class 0 OID 16503)
-- Dependencies: 230
-- Data for Name: tipos_descuento; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.tipos_descuento (id, nombre, descripcion, valor_descuento, activo, fecha_creacion) FROM stdin;
\.


--
-- TOC entry 4148 (class 0 OID 16652)
-- Dependencies: 240
-- Data for Name: tipos_movimiento_caja; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.tipos_movimiento_caja (id, nombre, naturaleza, activo, fecha_creacion) FROM stdin;
\.


--
-- TOC entry 4162 (class 0 OID 16812)
-- Dependencies: 254
-- Data for Name: tipos_movimiento_stock; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.tipos_movimiento_stock (id, nombre, descripcion, naturaleza, activo, fecha_creacion) FROM stdin;
\.


--
-- TOC entry 4152 (class 0 OID 16707)
-- Dependencies: 244
-- Data for Name: tipos_producto; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.tipos_producto (id, nombre, descripcion, activo, fecha_creacion) FROM stdin;
\.


--
-- TOC entry 4136 (class 0 OID 16486)
-- Dependencies: 228
-- Data for Name: tipos_venta; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.tipos_venta (id, nombre, descripcion, activo, fecha_creacion) FROM stdin;
\.


--
-- TOC entry 4156 (class 0 OID 16737)
-- Dependencies: 248
-- Data for Name: unidades_medida; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.unidades_medida (id, nombre, descripcion, activo, fecha_creacion) FROM stdin;
\.


--
-- TOC entry 4134 (class 0 OID 16446)
-- Dependencies: 226
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.usuarios (id, empleado_id, username, password_hash, rol_id, email, ultimo_login, estado_id, fecha_creacion) FROM stdin;
2	1	daniel.sanabria	hassh123	1	daniel.sanabria19@outlook.com	\N	1	2026-04-23 14:56:48.302333
\.


--
-- TOC entry 4144 (class 0 OID 16568)
-- Dependencies: 236
-- Data for Name: ventas; Type: TABLE DATA; Schema: public; Owner: daniel
--

COPY public.ventas (id, fecha, usuario_id, caja_id, metodo_pago_id, tipo_venta_id, subtotal, descuento, total, efectivo_recibido, cambio, observaciones, fecha_creacion) FROM stdin;
\.


--
-- TOC entry 4189 (class 0 OID 0)
-- Dependencies: 233
-- Name: cajas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.cajas_id_seq', 1, false);


--
-- TOC entry 4190 (class 0 OID 0)
-- Dependencies: 245
-- Name: categorias_producto_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.categorias_producto_id_seq', 1, false);


--
-- TOC entry 4191 (class 0 OID 0)
-- Dependencies: 237
-- Name: detalles_venta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.detalles_venta_id_seq', 1, false);


--
-- TOC entry 4192 (class 0 OID 0)
-- Dependencies: 223
-- Name: empleados_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.empleados_id_seq', 17, true);


--
-- TOC entry 4193 (class 0 OID 0)
-- Dependencies: 221
-- Name: estado_usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.estado_usuarios_id_seq', 3, true);


--
-- TOC entry 4194 (class 0 OID 0)
-- Dependencies: 231
-- Name: metodos_pago_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.metodos_pago_id_seq', 1, false);


--
-- TOC entry 4195 (class 0 OID 0)
-- Dependencies: 241
-- Name: movimientos_caja_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.movimientos_caja_id_seq', 1, false);


--
-- TOC entry 4196 (class 0 OID 0)
-- Dependencies: 255
-- Name: movimientos_stock_producto_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.movimientos_stock_producto_id_seq', 1, false);


--
-- TOC entry 4197 (class 0 OID 0)
-- Dependencies: 249
-- Name: productos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.productos_id_seq', 1, false);


--
-- TOC entry 4198 (class 0 OID 0)
-- Dependencies: 219
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.roles_id_seq', 3, true);


--
-- TOC entry 4199 (class 0 OID 0)
-- Dependencies: 251
-- Name: stock_producto_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.stock_producto_id_seq', 1, false);


--
-- TOC entry 4200 (class 0 OID 0)
-- Dependencies: 229
-- Name: tipos_descuento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.tipos_descuento_id_seq', 1, false);


--
-- TOC entry 4201 (class 0 OID 0)
-- Dependencies: 239
-- Name: tipos_movimiento_caja_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.tipos_movimiento_caja_id_seq', 1, false);


--
-- TOC entry 4202 (class 0 OID 0)
-- Dependencies: 253
-- Name: tipos_movimiento_stock_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.tipos_movimiento_stock_id_seq', 1, false);


--
-- TOC entry 4203 (class 0 OID 0)
-- Dependencies: 243
-- Name: tipos_producto_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.tipos_producto_id_seq', 1, false);


--
-- TOC entry 4204 (class 0 OID 0)
-- Dependencies: 227
-- Name: tipos_venta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.tipos_venta_id_seq', 1, false);


--
-- TOC entry 4205 (class 0 OID 0)
-- Dependencies: 247
-- Name: unidades_medida_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.unidades_medida_id_seq', 1, false);


--
-- TOC entry 4206 (class 0 OID 0)
-- Dependencies: 225
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 2, true);


--
-- TOC entry 4207 (class 0 OID 0)
-- Dependencies: 235
-- Name: ventas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: daniel
--

SELECT pg_catalog.setval('public.ventas_id_seq', 1, false);


--
-- TOC entry 3893 (class 2606 OID 16553)
-- Name: cajas cajas_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.cajas
    ADD CONSTRAINT cajas_pkey PRIMARY KEY (id);


--
-- TOC entry 3925 (class 2606 OID 16735)
-- Name: categorias_producto categorias_producto_nombre_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.categorias_producto
    ADD CONSTRAINT categorias_producto_nombre_key UNIQUE (nombre);


--
-- TOC entry 3927 (class 2606 OID 16733)
-- Name: categorias_producto categorias_producto_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.categorias_producto
    ADD CONSTRAINT categorias_producto_pkey PRIMARY KEY (id);


--
-- TOC entry 3905 (class 2606 OID 16636)
-- Name: detalles_venta detalles_venta_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.detalles_venta
    ADD CONSTRAINT detalles_venta_pkey PRIMARY KEY (id);


--
-- TOC entry 3865 (class 2606 OID 16442)
-- Name: empleados empleados_documento_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.empleados
    ADD CONSTRAINT empleados_documento_key UNIQUE (documento);


--
-- TOC entry 3867 (class 2606 OID 16444)
-- Name: empleados empleados_email_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.empleados
    ADD CONSTRAINT empleados_email_key UNIQUE (email);


--
-- TOC entry 3869 (class 2606 OID 16440)
-- Name: empleados empleados_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.empleados
    ADD CONSTRAINT empleados_pkey PRIMARY KEY (id);


--
-- TOC entry 3861 (class 2606 OID 16422)
-- Name: estados_usuarios estado_usuarios_nombre_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.estados_usuarios
    ADD CONSTRAINT estado_usuarios_nombre_key UNIQUE (nombre);


--
-- TOC entry 3863 (class 2606 OID 16420)
-- Name: estados_usuarios estado_usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.estados_usuarios
    ADD CONSTRAINT estado_usuarios_pkey PRIMARY KEY (id);


--
-- TOC entry 3889 (class 2606 OID 16536)
-- Name: metodos_pago metodos_pago_nombre_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.metodos_pago
    ADD CONSTRAINT metodos_pago_nombre_key UNIQUE (nombre);


--
-- TOC entry 3891 (class 2606 OID 16534)
-- Name: metodos_pago metodos_pago_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.metodos_pago
    ADD CONSTRAINT metodos_pago_pkey PRIMARY KEY (id);


--
-- TOC entry 3919 (class 2606 OID 16685)
-- Name: movimientos_caja movimientos_caja_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.movimientos_caja
    ADD CONSTRAINT movimientos_caja_pkey PRIMARY KEY (id);


--
-- TOC entry 3958 (class 2606 OID 16847)
-- Name: movimientos_stock_producto movimientos_stock_producto_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.movimientos_stock_producto
    ADD CONSTRAINT movimientos_stock_producto_pkey PRIMARY KEY (id);


--
-- TOC entry 3938 (class 2606 OID 16775)
-- Name: productos productos_codigo_barras_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_codigo_barras_key UNIQUE (codigo_barras);


--
-- TOC entry 3940 (class 2606 OID 16773)
-- Name: productos productos_nombre_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_nombre_key UNIQUE (nombre);


--
-- TOC entry 3942 (class 2606 OID 16771)
-- Name: productos productos_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_pkey PRIMARY KEY (id);


--
-- TOC entry 3857 (class 2606 OID 16405)
-- Name: roles roles_nombre_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_nombre_key UNIQUE (nombre);


--
-- TOC entry 3859 (class 2606 OID 16403)
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- TOC entry 3946 (class 2606 OID 16803)
-- Name: stock_producto stock_producto_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.stock_producto
    ADD CONSTRAINT stock_producto_pkey PRIMARY KEY (id);


--
-- TOC entry 3948 (class 2606 OID 16805)
-- Name: stock_producto stock_producto_producto_id_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.stock_producto
    ADD CONSTRAINT stock_producto_producto_id_key UNIQUE (producto_id);


--
-- TOC entry 3885 (class 2606 OID 16519)
-- Name: tipos_descuento tipos_descuento_nombre_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.tipos_descuento
    ADD CONSTRAINT tipos_descuento_nombre_key UNIQUE (nombre);


--
-- TOC entry 3887 (class 2606 OID 16517)
-- Name: tipos_descuento tipos_descuento_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.tipos_descuento
    ADD CONSTRAINT tipos_descuento_pkey PRIMARY KEY (id);


--
-- TOC entry 3911 (class 2606 OID 16667)
-- Name: tipos_movimiento_caja tipos_movimiento_caja_nombre_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.tipos_movimiento_caja
    ADD CONSTRAINT tipos_movimiento_caja_nombre_key UNIQUE (nombre);


--
-- TOC entry 3913 (class 2606 OID 16665)
-- Name: tipos_movimiento_caja tipos_movimiento_caja_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.tipos_movimiento_caja
    ADD CONSTRAINT tipos_movimiento_caja_pkey PRIMARY KEY (id);


--
-- TOC entry 3950 (class 2606 OID 16828)
-- Name: tipos_movimiento_stock tipos_movimiento_stock_nombre_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.tipos_movimiento_stock
    ADD CONSTRAINT tipos_movimiento_stock_nombre_key UNIQUE (nombre);


--
-- TOC entry 3952 (class 2606 OID 16826)
-- Name: tipos_movimiento_stock tipos_movimiento_stock_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.tipos_movimiento_stock
    ADD CONSTRAINT tipos_movimiento_stock_pkey PRIMARY KEY (id);


--
-- TOC entry 3921 (class 2606 OID 16720)
-- Name: tipos_producto tipos_producto_nombre_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.tipos_producto
    ADD CONSTRAINT tipos_producto_nombre_key UNIQUE (nombre);


--
-- TOC entry 3923 (class 2606 OID 16718)
-- Name: tipos_producto tipos_producto_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.tipos_producto
    ADD CONSTRAINT tipos_producto_pkey PRIMARY KEY (id);


--
-- TOC entry 3881 (class 2606 OID 16501)
-- Name: tipos_venta tipos_venta_nombre_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.tipos_venta
    ADD CONSTRAINT tipos_venta_nombre_key UNIQUE (nombre);


--
-- TOC entry 3883 (class 2606 OID 16499)
-- Name: tipos_venta tipos_venta_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.tipos_venta
    ADD CONSTRAINT tipos_venta_pkey PRIMARY KEY (id);


--
-- TOC entry 3929 (class 2606 OID 16750)
-- Name: unidades_medida unidades_medida_nombre_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.unidades_medida
    ADD CONSTRAINT unidades_medida_nombre_key UNIQUE (nombre);


--
-- TOC entry 3931 (class 2606 OID 16748)
-- Name: unidades_medida unidades_medida_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.unidades_medida
    ADD CONSTRAINT unidades_medida_pkey PRIMARY KEY (id);


--
-- TOC entry 3875 (class 2606 OID 16465)
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- TOC entry 3877 (class 2606 OID 16461)
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- TOC entry 3879 (class 2606 OID 16463)
-- Name: usuarios usuarios_username_key; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_username_key UNIQUE (username);


--
-- TOC entry 3903 (class 2606 OID 16589)
-- Name: ventas ventas_pkey; Type: CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT ventas_pkey PRIMARY KEY (id);


--
-- TOC entry 3894 (class 1259 OID 16566)
-- Name: idx_cajas_estado; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_cajas_estado ON public.cajas USING btree (estado);


--
-- TOC entry 3895 (class 1259 OID 16564)
-- Name: idx_cajas_usuario_apertura; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_cajas_usuario_apertura ON public.cajas USING btree (usuario_apertura_id);


--
-- TOC entry 3896 (class 1259 OID 16565)
-- Name: idx_cajas_usuario_cierre; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_cajas_usuario_cierre ON public.cajas USING btree (usuario_cierre_id);


--
-- TOC entry 3906 (class 1259 OID 16648)
-- Name: idx_detalles_venta_fecha_creacion; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_detalles_venta_fecha_creacion ON public.detalles_venta USING btree (fecha_creacion);


--
-- TOC entry 3907 (class 1259 OID 16647)
-- Name: idx_detalles_venta_producto_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_detalles_venta_producto_id ON public.detalles_venta USING btree (producto_id);


--
-- TOC entry 3908 (class 1259 OID 16649)
-- Name: idx_detalles_venta_tipo_descuento_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_detalles_venta_tipo_descuento_id ON public.detalles_venta USING btree (tipo_descuento_id);


--
-- TOC entry 3909 (class 1259 OID 16650)
-- Name: idx_detalles_venta_venta_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_detalles_venta_venta_id ON public.detalles_venta USING btree (venta_id);


--
-- TOC entry 3870 (class 1259 OID 16484)
-- Name: idx_empleados_nombre; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_empleados_nombre ON public.empleados USING btree (nombre);


--
-- TOC entry 3953 (class 1259 OID 16873)
-- Name: idx_mov_stock_fecha; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_mov_stock_fecha ON public.movimientos_stock_producto USING btree (fecha_creacion);


--
-- TOC entry 3954 (class 1259 OID 16870)
-- Name: idx_mov_stock_producto_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_mov_stock_producto_id ON public.movimientos_stock_producto USING btree (producto_id);


--
-- TOC entry 3955 (class 1259 OID 16871)
-- Name: idx_mov_stock_tipo_movimiento_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_mov_stock_tipo_movimiento_id ON public.movimientos_stock_producto USING btree (tipo_movimiento_id);


--
-- TOC entry 3956 (class 1259 OID 16872)
-- Name: idx_mov_stock_usuario_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_mov_stock_usuario_id ON public.movimientos_stock_producto USING btree (usuario_id);


--
-- TOC entry 3914 (class 1259 OID 16701)
-- Name: idx_movimientos_caja_caja_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_movimientos_caja_caja_id ON public.movimientos_caja USING btree (caja_id);


--
-- TOC entry 3915 (class 1259 OID 16704)
-- Name: idx_movimientos_caja_fecha; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_movimientos_caja_fecha ON public.movimientos_caja USING btree (fecha_creacion);


--
-- TOC entry 3916 (class 1259 OID 16703)
-- Name: idx_movimientos_caja_tipo_movimiento_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_movimientos_caja_tipo_movimiento_id ON public.movimientos_caja USING btree (tipo_movimiento_id);


--
-- TOC entry 3917 (class 1259 OID 16702)
-- Name: idx_movimientos_caja_usuario_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_movimientos_caja_usuario_id ON public.movimientos_caja USING btree (usuario_id);


--
-- TOC entry 3932 (class 1259 OID 16867)
-- Name: idx_productos_activo; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_productos_activo ON public.productos USING btree (activo);


--
-- TOC entry 3933 (class 1259 OID 16864)
-- Name: idx_productos_categoria_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_productos_categoria_id ON public.productos USING btree (categoria_id);


--
-- TOC entry 3934 (class 1259 OID 16863)
-- Name: idx_productos_nombre; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_productos_nombre ON public.productos USING btree (nombre);


--
-- TOC entry 3935 (class 1259 OID 16865)
-- Name: idx_productos_tipo_producto_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_productos_tipo_producto_id ON public.productos USING btree (tipo_producto_id);


--
-- TOC entry 3936 (class 1259 OID 16866)
-- Name: idx_productos_unidad_medida_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_productos_unidad_medida_id ON public.productos USING btree (unidad_medida_id);


--
-- TOC entry 3943 (class 1259 OID 16869)
-- Name: idx_stock_producto_fecha_actualizacion; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_stock_producto_fecha_actualizacion ON public.stock_producto USING btree (fecha_ultima_actualizacion);


--
-- TOC entry 3944 (class 1259 OID 16868)
-- Name: idx_stock_producto_producto_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_stock_producto_producto_id ON public.stock_producto USING btree (producto_id);


--
-- TOC entry 3871 (class 1259 OID 16481)
-- Name: idx_usuarios_empleado_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_usuarios_empleado_id ON public.usuarios USING btree (empleado_id);


--
-- TOC entry 3872 (class 1259 OID 16483)
-- Name: idx_usuarios_estado_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_usuarios_estado_id ON public.usuarios USING btree (estado_id);


--
-- TOC entry 3873 (class 1259 OID 16482)
-- Name: idx_usuarios_rol_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_usuarios_rol_id ON public.usuarios USING btree (rol_id);


--
-- TOC entry 3897 (class 1259 OID 16613)
-- Name: idx_ventas_caja_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_ventas_caja_id ON public.ventas USING btree (caja_id);


--
-- TOC entry 3898 (class 1259 OID 16610)
-- Name: idx_ventas_fecha; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_ventas_fecha ON public.ventas USING btree (fecha);


--
-- TOC entry 3899 (class 1259 OID 16614)
-- Name: idx_ventas_metodo_pago_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_ventas_metodo_pago_id ON public.ventas USING btree (metodo_pago_id);


--
-- TOC entry 3900 (class 1259 OID 16612)
-- Name: idx_ventas_tipo_venta_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_ventas_tipo_venta_id ON public.ventas USING btree (tipo_venta_id);


--
-- TOC entry 3901 (class 1259 OID 16611)
-- Name: idx_ventas_usuario_id; Type: INDEX; Schema: public; Owner: daniel
--

CREATE INDEX idx_ventas_usuario_id ON public.ventas USING btree (usuario_id);


--
-- TOC entry 3962 (class 2606 OID 16554)
-- Name: cajas fk_caja_usuario_apertura; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.cajas
    ADD CONSTRAINT fk_caja_usuario_apertura FOREIGN KEY (usuario_apertura_id) REFERENCES public.usuarios(id);


--
-- TOC entry 3963 (class 2606 OID 16559)
-- Name: cajas fk_caja_usuario_cierre; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.cajas
    ADD CONSTRAINT fk_caja_usuario_cierre FOREIGN KEY (usuario_cierre_id) REFERENCES public.usuarios(id);


--
-- TOC entry 3968 (class 2606 OID 16642)
-- Name: detalles_venta fk_detalle_venta_tipo_descuento; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.detalles_venta
    ADD CONSTRAINT fk_detalle_venta_tipo_descuento FOREIGN KEY (tipo_descuento_id) REFERENCES public.tipos_descuento(id);


--
-- TOC entry 3969 (class 2606 OID 16637)
-- Name: detalles_venta fk_detalle_venta_venta; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.detalles_venta
    ADD CONSTRAINT fk_detalle_venta_venta FOREIGN KEY (venta_id) REFERENCES public.ventas(id);


--
-- TOC entry 3970 (class 2606 OID 16686)
-- Name: movimientos_caja fk_mov_caja; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.movimientos_caja
    ADD CONSTRAINT fk_mov_caja FOREIGN KEY (caja_id) REFERENCES public.cajas(id);


--
-- TOC entry 3971 (class 2606 OID 16696)
-- Name: movimientos_caja fk_mov_tipo; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.movimientos_caja
    ADD CONSTRAINT fk_mov_tipo FOREIGN KEY (tipo_movimiento_id) REFERENCES public.tipos_movimiento_caja(id);


--
-- TOC entry 3972 (class 2606 OID 16691)
-- Name: movimientos_caja fk_mov_usuario; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.movimientos_caja
    ADD CONSTRAINT fk_mov_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- TOC entry 3977 (class 2606 OID 16848)
-- Name: movimientos_stock_producto fk_movimientos_stock_producto_producto; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.movimientos_stock_producto
    ADD CONSTRAINT fk_movimientos_stock_producto_producto FOREIGN KEY (producto_id) REFERENCES public.productos(id);


--
-- TOC entry 3978 (class 2606 OID 16853)
-- Name: movimientos_stock_producto fk_movimientos_stock_producto_tipo_movimiento; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.movimientos_stock_producto
    ADD CONSTRAINT fk_movimientos_stock_producto_tipo_movimiento FOREIGN KEY (tipo_movimiento_id) REFERENCES public.tipos_movimiento_stock(id);


--
-- TOC entry 3979 (class 2606 OID 16858)
-- Name: movimientos_stock_producto fk_movimientos_stock_producto_usuarios; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.movimientos_stock_producto
    ADD CONSTRAINT fk_movimientos_stock_producto_usuarios FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- TOC entry 3973 (class 2606 OID 16776)
-- Name: productos fk_producto_categoria; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT fk_producto_categoria FOREIGN KEY (categoria_id) REFERENCES public.categorias_producto(id);


--
-- TOC entry 3974 (class 2606 OID 16781)
-- Name: productos fk_producto_tipo_producto; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT fk_producto_tipo_producto FOREIGN KEY (tipo_producto_id) REFERENCES public.tipos_producto(id);


--
-- TOC entry 3975 (class 2606 OID 16786)
-- Name: productos fk_producto_unidad_medida; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT fk_producto_unidad_medida FOREIGN KEY (unidad_medida_id) REFERENCES public.unidades_medida(id);


--
-- TOC entry 3976 (class 2606 OID 16806)
-- Name: stock_producto fk_stock_producto_producto; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.stock_producto
    ADD CONSTRAINT fk_stock_producto_producto FOREIGN KEY (producto_id) REFERENCES public.productos(id);


--
-- TOC entry 3959 (class 2606 OID 16466)
-- Name: usuarios fk_usuario_empleado; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT fk_usuario_empleado FOREIGN KEY (empleado_id) REFERENCES public.empleados(id);


--
-- TOC entry 3960 (class 2606 OID 16476)
-- Name: usuarios fk_usuario_estado; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT fk_usuario_estado FOREIGN KEY (estado_id) REFERENCES public.estados_usuarios(id);


--
-- TOC entry 3961 (class 2606 OID 16471)
-- Name: usuarios fk_usuario_rol; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT fk_usuario_rol FOREIGN KEY (rol_id) REFERENCES public.roles(id);


--
-- TOC entry 3964 (class 2606 OID 16605)
-- Name: ventas fk_ventas_caja; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT fk_ventas_caja FOREIGN KEY (caja_id) REFERENCES public.cajas(id);


--
-- TOC entry 3965 (class 2606 OID 16595)
-- Name: ventas fk_ventas_metodo_pago; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT fk_ventas_metodo_pago FOREIGN KEY (metodo_pago_id) REFERENCES public.metodos_pago(id);


--
-- TOC entry 3966 (class 2606 OID 16600)
-- Name: ventas fk_ventas_tipo_venta; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT fk_ventas_tipo_venta FOREIGN KEY (tipo_venta_id) REFERENCES public.tipos_venta(id);


--
-- TOC entry 3967 (class 2606 OID 16590)
-- Name: ventas fk_ventas_usuario; Type: FK CONSTRAINT; Schema: public; Owner: daniel
--

ALTER TABLE ONLY public.ventas
    ADD CONSTRAINT fk_ventas_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


-- Completed on 2026-04-24 20:17:06 -05

--
-- PostgreSQL database dump complete
--

\unrestrict Ugwku8nRxetd7qatMLmYtzAFHLyqhVCqlZVslJ6q3HcUgAhho16Ly8Dnejb0gYf

