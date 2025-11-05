// js/config.js (MODIFICADO)
window.PRESTALAB = {
  // YA NO USAMOS ESTOS:
  // BUS_BASE_URL: "http://localhost:8000",
  // ROUTE_PATH: "/route",
  
  // AHORA USAMOS ESTE:
  // Esta es la URL de tu "Traductor" (el script gateway.py)
  GATEWAY_URL: "http://localhost:8001/route",

  DEFAULT_TIMEOUT: 30,
  DEBUG_BUS: true,

  // Servicios (nombres lógicos registrados en el Bus)
  // ESTO SE MANTIENE EXACTAMENTE IGUAL
  SERVICES: {
    REPORTS: "gerep",
    WAITLIST: "lista",     
    FINES: "multa",
    NOTIFICATIONS: "notis",
    CATALOG: "prart",      
    AUTH: "regist",
    SUGGESTIONS: "sugit",  
    SUGGEST: "sugit" // Mantener alias
  },

  // Flags y permisos (SE MANTIENE IGUAL)
  FEATURES: {
    MY_LOANS: true
  },
  ADMIN_EMAILS: ["admin.prestalab@udp.cl"]
};