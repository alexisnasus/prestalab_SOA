CREATE TABLE item
  (
    id               bigint        auto_increment unique not null,
    nombre           varchar(50)  not null,
    cantidad         int          not null,
    tipo             varchar(20)  not null,
    valor            decimal(10,2) not null, CHECK (valor >= 0),
    tarifa_atraso    decimal(10,2) not null, CHECK (tarifa_atraso >= 0),
    descripcion      varchar(100) not null,
    cantidad_max     int          not null, CHECK (cantidad_max > 0),
    registro_instante datetime     not null,

    primary key(id)
  )
ENGINE = InnoDB;

CREATE INDEX itemIDX1 ON item(nombre, tipo);

-- ----------------------------------------------------------------------

#TIPO: LIBRO, REVISTA, EQUIPO_ELECTRONICO, OTRO

-- ======================================================================

CREATE TABLE sede
  (
    id               bigint        auto_increment unique not null,
    nombre           varchar(50)  not null,

    primary key(id)
  )
ENGINE = InnoDB;

-- ======================================================================

CREATE TABLE item_existencia
  (
    id               bigint        auto_increment unique not null,
    item_id          bigint        not null,
    sede_id          bigint        not null,
    codigo           varchar(50)   unique not null,
    estado           varchar(20)   not null,
    registro_instante datetime     not null,

    primary key(id),
    foreign key(item_id) references item(id),
    foreign key(sede_id) references sede(id),
    unique(codigo)
  )
ENGINE = InnoDB;

CREATE INDEX item_existenciaIDX1 ON item_existencia(item_id);

-- ----------------------------------------------------------------------

#ESTADO: DISPONIBLE, PRESTADO, MANTENIMIENTO, PERDIDO, DANNADO, ROBADO

-- ======================================================================

CREATE TABLE usuario
  (
    id               bigint        auto_increment unique not null,
    nombre           varchar(50)  not null,
    correo           varchar(50)  unique not null,
    tipo             varchar(20)  not null,
    telefono         varchar(15)  null default '',
    password         varchar(128) not null,
    estado           varchar(20)  not null default 'ACTIVO',
    preferencias_notificacion int not null default 1,
    registro_instante datetime     not null default CURRENT_TIMESTAMP,

    primary key(id),
    unique(correo)
  )
ENGINE = InnoDB;

CREATE INDEX usuarioIDX1 ON usuario(nombre);

-- ----------------------------------------------------------------------

#TIPO: ENCARGADO, ESTUDIANTE, DOCENTE
#ESTADO: ACTIVO, INACTIVO, SUSPENDIDO, DEUDOR, BLOQUEADO
#PREFERENCIAS_NOTIFICACION: 1=PORTAL, 2=WHATSAPP, 3=EMAIL

-- ======================================================================

CREATE TABLE sugerencia
  (
    id               bigint        auto_increment unique not null,
    usuario_id       bigint        not null,
    sugerencia       varchar(100)  not null,
    estado           varchar(20)   not null,
    registro_instante datetime     not null,

    primary key(id),
    foreign key(usuario_id) references usuario(id)
  )
ENGINE = InnoDB;

-- ----------------------------------------------------------------------

#ESTADO: PENDIENTE, ACEPTADA, RECHAZADA

-- ======================================================================

CREATE TABLE notificacion
  (
    id               bigint        auto_increment unique not null,
    usuario_id       bigint        not null,
    canal            int   not null,
    tipo             varchar(20)   not null,
    mensaje          text          not null,
    registro_instante datetime     not null,

    primary key(id),
    foreign key(usuario_id) references usuario(id)
  )
ENGINE = InnoDB;

CREATE INDEX notificacionIDX1 ON notificacion(usuario_id);

-- ----------------------------------------------------------------------

#CANAL: 1=PORTAL, 2=WHATSAPP, 3=EMAIL
#TIPO: RECORDATORIO, LISTA_ESPERA, SUGERENCIA_ACEPTADA, SUGERENCIA_RECHAZADA, ATRASO, RESERVA_CREADA, RESERVA_PROXIMA_CADUCAR, RESERVA_CADUCADA, PRESTAMO_CONFIRMADO, DEVOLUCION_PROXIMA

-- ======================================================================

CREATE TABLE solicitud
  (
    id               bigint        auto_increment unique not null,
    usuario_id       bigint        not null,
    tipo             varchar(30)   not null,
    estado           varchar(20)   not null,
    registro_instante datetime     not null,

    primary key(id),
    foreign key(usuario_id) references usuario(id)
  )
ENGINE = InnoDB;

CREATE INDEX solicitudIDX1 ON solicitud(usuario_id);

-- ----------------------------------------------------------------------

#TIPO: VENTANA, PRESTAMO, RENOVACION
#ESTADO: PENDIENTE, APROBADA, RECHAZADA

-- ======================================================================

CREATE TABLE item_solicitud
  (
    solicitud_id     bigint        not null,
    item_id          bigint        not null,
    cantidad         int           not null CHECK (cantidad > 0),
    registro_instante datetime     not null,

    primary key(solicitud_id, item_id),
    foreign key(solicitud_id) references solicitud(id),
    foreign key(item_id) references item(id)
  )
ENGINE = InnoDB;

CREATE INDEX item_solicitudIDX1 ON item_solicitud(item_id);

-- ----------------------------------------------------------------------

-- ======================================================================

CREATE TABLE prestamo
  (
    id               bigint        auto_increment unique not null,
    item_existencia_id bigint      not null,
    solicitud_id     bigint        not null,
    fecha_prestamo   datetime      not null,
    fecha_devolucion datetime      null,
    comentario       text          null,
    estado           varchar(20)   not null,
    renovaciones_realizadas int    not null default 0,
    registro_instante datetime     not null,

    primary key(id),
    foreign key(item_existencia_id) references item_existencia(id),
    foreign key(solicitud_id) references solicitud(id)
  )
ENGINE = InnoDB;

CREATE INDEX prestamoIDX1 ON prestamo(item_existencia_id);

-- ----------------------------------------------------------------------

#ESTADO: ACTIVO, DEVUELTO, VENCIDO, PERDIDO

-- ======================================================================

CREATE TABLE atraso
  (
    id               bigint        auto_increment unique not null,
    prestamo_id      bigint        not null,
    dias_atraso      int           not null CHECK (dias_atraso > 0),
    estado           varchar(20)   not null,
    registro_instante datetime     not null,

    primary key(id),
    foreign key(prestamo_id) references prestamo(id)
  )
ENGINE = InnoDB;

CREATE INDEX atrasoIDX1 ON atraso(prestamo_id);

-- ----------------------------------------------------------------------

#ESTADO: PENDIENTE, NOTIFICADO, PAGADO, NO_PAGADO

-- ======================================================================

CREATE TABLE multa
  (
    id               bigint        auto_increment unique not null,
    prestamo_id      bigint        not null,
    motivo           varchar(20)  not null,
    valor            decimal(10,2) not null CHECK (valor > 0),
    estado           varchar(20)   not null,
    registro_instante datetime     not null,

    primary key(id),
    foreign key(prestamo_id) references prestamo(id)
  )
ENGINE = InnoDB;

CREATE INDEX multaIDX1 ON multa(prestamo_id);

-- ----------------------------------------------------------------------

#ESTADO: PENDIENTE, NOTIFICADO, PAGADO, NO_PAGADO
#MOTIVO: ATRASO, DANNOS, ROBO, PERDIDA

-- ======================================================================

CREATE TABLE ventana
  (
    id                 bigint        auto_increment unique not null,
    solicitud_id       bigint        not null,
    item_existencia_id bigint        not null,  
    inicio             datetime      not null,
    fin                datetime      not null,

    primary key(id),
    foreign key(solicitud_id) references solicitud(id),
    foreign key(item_existencia_id) references item_existencia(id),
    CHECK (fin > inicio)
  )
ENGINE = InnoDB;

-- ----------------------------------------------------------------------

-- ======================================================================

CREATE TABLE lista_espera
  (
    id               bigint        auto_increment unique not null,
    solicitud_id     bigint        not null,
    item_id          bigint        not null,
    fecha_ingreso    datetime      not null,
    estado           varchar(20)   not null,
    registro_instante datetime     not null,

    primary key(id),
    foreign key(solicitud_id) references solicitud(id),
    foreign key(item_id) references item(id)
  )
ENGINE = InnoDB;

CREATE INDEX lista_esperaIDX3 ON lista_espera(fecha_ingreso);


-- ----------------------------------------------------------------------

#ESTADO: EN_ESPERA, CANCELADA, ATENDIDA

-- ======================================================================

CREATE TABLE configuracion_sistema
  (
    id               bigint        auto_increment unique not null,
    clave            varchar(50)   unique not null,
    valor            varchar(100)  not null,
    descripcion      text          null,
    registro_instante datetime     not null,

    primary key(id),
    unique(clave)
  )
ENGINE = InnoDB;

-- ----------------------------------------------------------------------

#EJEMPLOS DE CONFIGURACIONES (LLAVES Y EJEMPLOS DE VALORES):
#max_renovaciones_usuario: 3
#dias_max_atraso_robo: 30
#horas_expiracion_reserva: 24
#tarifa_base_multa: 5000.00
#dias_notificacion_devolucion_proxima: 3
#dias_notificacion_reserva_proxima_caducar: 1
#max_items_por_usuario: 5
#dias_suspension_por_atraso: 15
#valor_multa_por_dia_atraso: 1000.00
#porcentaje_multa_danos: 50
#porcentaje_multa_perdida: 100
#porcentaje_multa_robo: 100
#dias_gracia_devolucion: 1
#max_items_reserva_simultanea: 3
#tiempo_bloqueo_usuario_deudor_dias: 30
#notificar_atraso_cada_dias: 7

-- ======================================================================
















