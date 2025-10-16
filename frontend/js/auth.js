// auth.js — Manejo de sesión para PrestaLab (CORREGIDO)
(function () {
  const LS_TOKEN = "pl_token";
  const LS_USER  = "pl_user";
  const LS_UID   = "pl_user_id";

  function saveSession(token, user) {
    localStorage.setItem(LS_TOKEN, token);
    localStorage.setItem(LS_USER, JSON.stringify(user || null));

    if (user?.id && /^\d+$/.test(String(user.id))) {
      localStorage.setItem(LS_UID, String(user.id));
      console.log(`[AUTH] ID de usuario ${user.id} guardado en la sesión.`);
    } else {
      console.warn("[AUTH] El objeto de usuario no contenía un ID numérico.");
    }
  }

  function clearSession() {
    localStorage.removeItem(LS_TOKEN);
    localStorage.removeItem(LS_USER);
    localStorage.removeItem(LS_UID);
  }

  function getToken() { return localStorage.getItem(LS_TOKEN) || ""; }
  function getUser() { try { return JSON.parse(localStorage.getItem(LS_USER) || "null"); } catch { return null; } }
  function getEmail() { const u = getUser(); return (u?.correo || "").toLowerCase(); }
  function getUserId() {
    const id = localStorage.getItem(LS_UID);
    return id && /^\d+$/.test(id) ? Number(id) : null;
  }

  async function login(correo, password) {
    const S = window.PRESTALAB?.SERVICES || {};
    const res = await window.API.post(S.AUTH, "/auth/login", { correo, password }, { auth: false });
    if (!res || !res.token) throw new Error("Respuesta de login inválida");
    const user = res.user || { correo }; 
    saveSession(res.token, user);
    return res;
  }

  function logout() { clearSession(); location.href = "index.html"; }
  function requireAuth() { if (!getToken()) location.href = "index.html"; }

  window.Auth = { login, logout, getToken, getUser, getEmail, getUserId, requireAuth };
  console.log("[AUTH] Módulo de autenticación listo.");
})();