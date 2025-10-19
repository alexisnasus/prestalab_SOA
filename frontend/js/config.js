// js/config.js
window.PRESTALAB = {
  // ESB (Bus)
  BUS_BASE_URL: "http://localhost:8000",
  ROUTE_PATH: "/route",
  DEFAULT_TIMEOUT: 30,
  DEBUG_BUS: true,

  // Servicios (nombres lógicos registrados en el Bus)
  SERVICES: {
    REPORTS: "gerep",
    WAITLIST: "lista",     
    FINES: "multa",
    NOTIFICATIONS: "notis",
    CATALOG: "prart",      
    AUTH: "regist",
    SUGGESTIONS: "sugit",  
    SUGGEST: "sugit"
  },

  // Flags y permisos
  FEATURES: {
    MY_LOANS: true
  },
  ADMIN_EMAILS: ["admin.prestalab@udp.cl"]
};
