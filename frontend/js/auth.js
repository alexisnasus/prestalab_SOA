// auth.js — Sesión basada en correo (sin resolver ID)
(function () {
  const LS_TOKEN = "pl_token";
  const LS_USER  = "pl_user";
  const LS_UID   = "pl_user_id"; // lo dejaremos de usar, pero lo limpiamos por si quedó

  const S = window.PRESTALAB?.SERVICES || {};

  // -------------------- helpers de sesión --------------------
  function saveSession(token, user) {
    localStorage.setItem(LS_TOKEN, token);
    localStorage.setItem(LS_USER, JSON.stringify(user || null));
    // borramos cualquier “id” antiguo
    localStorage.removeItem(LS_UID);
  }
  function clearSession() {
    localStorage.removeItem(LS_TOKEN);
    localStorage.removeItem(LS_USER);
    localStorage.removeItem(LS_UID);
  }
  function getToken() { return localStorage.getItem(LS_TOKEN) || ""; }
  function getUser() {
    try { return JSON.parse(localStorage.getItem(LS_USER) || "null"); }
    catch { return null; }
  }
  function getEmail() {
    return (getUser()?.correo || "").toLowerCase();
  }

  // -------------------- login/logout --------------------
  // El backend valida: { correo, password: "mock_password" }
  async function login(correo, password) {
    const payload = { correo, password };
    const res = await window.API.post(S.AUTH, "/auth/login", payload, { auth: false });
    if (!res || !res.token || !res.user) throw new Error("Respuesta de login inválida");
    saveSession(res.token, res.user);
    return res;
  }

  function logout() { clearSession(); location.href = "index.html"; }
  function requireAuth() { if (!getToken()) location.href = "index.html"; }

  // API pública
  window.Auth = { login, logout, getToken, getUser, getEmail, requireAuth };
  console.log("[AUTH] Listo · sesión por correo");
})();
