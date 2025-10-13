// Config del Front para hablar SIEMPRE con el Bus ESB
window.PRESTALAB = {
  // URL base del Bus (no pongas /bus al final)
  BUS_BASE_URL: "http://localhost:8000",

  // Nombres lógicos registrados en el Bus (tal cual en tus servicios)
  SERVICES: {
    REPORTS: "gerep",
    WAITLIST: "lista",
    FINES: "multa",
    NOTIFICATIONS: "notis",
    CATALOG: "prart",
    AUTH: "regist",
    SUGGESTIONS: "sugit",
  },

  // Endpoint del Bus para enrutar mensajes
  ROUTE_PATH: "/route",

  // Timeout por defecto (seg)
  DEFAULT_TIMEOUT: 30,

  DEBUG_BUS: true
};

window.PRESTALAB.FEATURES = Object.assign(window.PRESTALAB.FEATURES||{}, {
  MY_LOANS: true
});

// js/config.js
window.PRESTALAB = {
  BUS_BASE_URL: "http://localhost:8000",   // URL del Bus (ESB)

  // Nombres lógicos 
  SERVICES: {
    REPORTS: "gerep",
    WAITLIST: "lista",
    FINES: "multa",
    NOTIFICATIONS: "notis",
    CATALOG: "prart",   // <-- importante: nombre, no URL
    AUTH: "regist",     // <-- importante: nombre, no URL
    SUGGESTIONS: "sugit",
  },

  ROUTE_PATH: "/route",
  DEFAULT_TIMEOUT: 30,
  DEBUG_BUS: true,

  // opcional: lista de correos con permisos de admin en el front
  ADMIN_EMAILS: ["admin.prestalab@udp.cl"]
};


