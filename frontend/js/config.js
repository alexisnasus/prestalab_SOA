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
};
