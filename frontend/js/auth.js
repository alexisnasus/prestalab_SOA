// auth.js — Manejo de sesión para PrestaLab
(function () {
  const LS_TOKEN = "pl_token";
  const LS_USER  = "pl_user";
  const LS_UID   = "pl_user_id"; // nuevo: para almacenar el ID del usuario

  // ---------- Helpers de sesión ----------
  function saveSession(token, user) {
    localStorage.setItem(LS_TOKEN, token);
    localStorage.setItem(LS_USER, JSON.stringify(user || null));

    // Guardar el ID si viene definido y es numérico
    if (user?.id && /^\d+$/.test(String(user.id))) {
      localStorage.setItem(LS_UID, String(user.id));
      console.log(`[AUTH] Usuario ID guardado: ${user.id}`);
    } else {
      console.warn("[AUTH] No se encontró ID en el usuario, se omitió guardado.");
    }
  }

  function clearSession() {
    localStorage.removeItem(LS_TOKEN);
    localStorage.removeItem(LS_USER);
    localStorage.removeItem(LS_UID);
  }

  function getToken() { 
    return localStorage.getItem(LS_TOKEN) || ""; 
  }

  function getUser() {
    try { 
      return JSON.parse(localStorage.getItem(LS_USER) || "null"); 
    } catch { 
      return null; 
    }
  }

  function getEmail() {
    const u = getUser();
    return (u?.correo || "").toLowerCase();
  }

  function getUserId() {
    const id = localStorage.getItem(LS_UID);
    return id && /^\d+$/.test(id) ? Number(id) : null;
  }

  // ---------- Login ----------
  async function login(correo, password) {
    const S = window.PRESTALAB?.SERVICES || {};
    const payload = { correo, password };

    // Ajusta el endpoint 
    const res = await window.API.post(S.AUTH, "/auth/login", payload, { auth: false });

    // Espera { token, usuario?: {...} }
    if (!res || !res.token) throw new Error("Respuesta de login inválida");

    // Si el backend devuelve datos del usuario,se guardan; si no, crea un objeto mínimo
    const user = res.usuario || { correo };
    saveSession(res.token, user);

    return res;
  }

  // ---------- Logout ----------
  function logout() {
    clearSession();
    location.href = "index.html";
  }

  // ---------- Protección ----------
  function requireAuth() {
    if (!getToken()) location.href = "index.html";
  }

  // ---------- Exponer API global ----------
  window.Auth = { 
    login, 
    logout, 
    getToken, 
    getUser, 
    getEmail, 
    getUserId,
    requireAuth 
  };

  console.log("[AUTH] Listo · sesión por correo + password");
})();
