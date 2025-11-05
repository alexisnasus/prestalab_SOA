// js/api.js (TOTALMENTE REEMPLAZADO)
(function () {
  const CFG = window.PRESTALAB || {};
  const S = CFG.SERVICES || {}; // Nombres de servicios (ej: S.AUTH es "regist")
  const GATEWAY_URL = CFG.GATEWAY_URL;
  
  if (!GATEWAY_URL) {
    console.error("FATAL: window.PRESTALAB.GATEWAY_URL no está definida en config.js");
    alert("Error de configuración: GATEWAY_URL no encontrada.");
    return;
  }

  /**
   * Esta es la NUEVA función base.
   * Envía una solicitud al Gateway, que la traducirá al bus TCP.
   * @param {string} service - Nombre del servicio (ej: "regis")
   * @param {string} operation - Operación del servicio (ej: "login")
   * @param {object} payload - Cuerpo JSON de la solicitud
   */
  async function sendToGateway(service, operation, payload = {}) {
    if (!service || !operation) {
      throw new Error("sendToGateway requiere 'service' y 'operation'");
    }

    const requestBody = {
      service: service,
      operation: operation,
      payload: payload
    };

    if (CFG.DEBUG_BUS) {
      console.debug(`[Gateway→] ${GATEWAY_URL}`, requestBody);
    }

    const res = await fetch(GATEWAY_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        // Aquí se podría añadir un Token de autenticación si se implementara
        // "Authorization": `Bearer ${window.Auth?.getToken?.()}`
      },
      body: JSON.stringify(requestBody),
      mode: "cors",
    });

    const responseData = await res.json().catch(() => ({}));

    if (CFG.DEBUG_BUS) {
      console.debug(`[Gateway←]`, { status: res.status, body: responseData });
    }

    if (!res.ok) {
      // Si el gateway o el bus fallaron, 'detail' contendrá el error
      const errorMsg = responseData.detail || responseData.error || res.statusText || "Error desconocido";
      const err = new Error(errorMsg);
      err.status = res.status;
      err.payload = responseData;
      
      // Deslogueo automático si es un error de autenticación
      if (err.status === 401 || err.status === 403) {
        try { window.Auth?.logout?.(); } catch {}
      }
      throw err;
    }

    return responseData; // Devuelve el JSON limpio del servicio
  }

  // --- MAPEO DE TODAS LAS OPERACIONES DE TUS SERVICIOS ---
  // (Basado en tus archivos app.py y test_*.py)
  
  window.API = {
    // Servicio: regist (S.AUTH)
    login: (payload) => sendToGateway(S.AUTH, "login", payload),
    register: (payload) => sendToGateway(S.AUTH, "register", payload),
    getUser: (payload) => sendToGateway(S.AUTH, "get_user", payload),
    updateUser: (payload) => sendToGateway(S.AUTH, "update_user", payload),
    updateSolicitud: (payload) => sendToGateway(S.AUTH, "update_solicitud", payload),

    // Servicio: prart (S.CATALOG)
    getAllItems: (payload = {}) => sendToGateway(S.CATALOG, "get_all_items", payload),
    searchItems: (payload) => sendToGateway(S.CATALOG, "search_items", payload),
    getSolicitudes: (payload) => sendToGateway(S.CATALOG, "get_solicitudes", payload),
    createSolicitud: (payload) => sendToGateway(S.CATALOG, "create_solicitud", payload),
    createReserva: (payload) => sendToGateway(S.CATALOG, "create_reserva", payload),
    cancelReserva: (payload) => sendToGateway(S.CATALOG, "cancel_reserva", payload),
    createPrestamo: (payload) => sendToGateway(S.CATALOG, "create_prestamo", payload),
    createDevolucion: (payload) => sendToGateway(S.CATALOG, "create_devolucion", payload),
    renovarPrestamo: (payload) => sendToGateway(S.CATALOG, "renovar_prestamo", payload),
    updateItemEstado: (payload) => sendToGateway(S.CATALOG, "update_item_estado", payload),

    // Servicio: lista (S.WAITLIST)
    createListaEspera: (payload) => sendToGateway(S.WAITLIST, "create_lista_espera", payload),
    updateListaEspera: (payload) => sendToGateway(S.WAITLIST, "update_lista_espera", payload),
    getListaEspera: (payload) => sendToGateway(S.WAITLIST, "get_lista_espera", payload),

    // Servicio: multa (S.FINES)
    getMultasUsuario: (payload) => sendToGateway(S.FINES, "get_multas_usuario", payload),
    crearMulta: (payload) => sendToGateway(S.FINES, "crear_multa", payload),
    updateBloqueo: (payload) => sendToGateway(S.FINES, "update_bloqueo", payload),

    // Servicio: notis (S.NOTIFICATIONS)
    crearNotificacion: (payload) => sendToGateway(S.NOTIFICATIONS, "crear_notificacion", payload),
    getPreferencias: (payload) => sendToGateway(S.NOTIFICATIONS, "get_preferencias", payload),
    updatePreferencias: (payload) => sendToGateway(S.NOTIFICATIONS, "update_preferencias", payload),

    // Servicio: gerep (S.REPORTS)
    getHistorial: (payload) => sendToGateway(S.REPORTS, "get_historial", payload),
    getReporteCirculacion: (payload) => sendToGateway(S.REPORTS, "get_reporte_circulacion", payload),

    // Servicio: sugit (S.SUGGESTIONS)
    registrarSugerencia: (payload) => sendToGateway(S.SUGGESTIONS, "registrar_sugerencia", payload),
    listarSugerencias: (payload = {}) => sendToGateway(S.SUGGESTIONS, "listar_sugerencias", payload),
    aprobarSugerencia: (payload) => sendToGateway(S.SUGGESTIONS, "aprobar_sugerencia", payload),
    rechazarSugerencia: (payload) => sendToGateway(S.SUGGESTIONS, "rechazar_sugerencia", payload)
  };
  
  console.log("[API] Adaptador Gateway-TCP listo.", { GATEWAY: GATEWAY_URL, SERVICES: S });
})();