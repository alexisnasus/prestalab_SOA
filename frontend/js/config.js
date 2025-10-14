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
    WAITLIST: "lista",     // ← lista de espera
    FINES: "multa",
    NOTIFICATIONS: "notis",
    CATALOG: "prart",      // ← catálogo / existencias
    AUTH: "regist",
    SUGGESTIONS: "sugit",  // ← como lo tienes en el Bus
    // Alias opcional para que el front lo encuentre sin tocar JS:
    SUGGEST: "sugit"
  },

  // Flags y permisos
  FEATURES: {
    MY_LOANS: true
  },
  ADMIN_EMAILS: ["admin.prestalab@udp.cl"]
};
