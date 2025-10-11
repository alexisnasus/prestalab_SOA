// auth.js
(function () {
  const LS_TOKEN = "pl_token";
  const LS_USER  = "pl_user";

  function saveSession(token, user) {
    localStorage.setItem(LS_TOKEN, token);
    localStorage.setItem(LS_USER, JSON.stringify(user || null));
  }
  function clearSession() {
    localStorage.removeItem(LS_TOKEN);
    localStorage.removeItem(LS_USER);
  }
  function getToken() { return localStorage.getItem(LS_TOKEN) || ""; }
  function getUser()  {
    try { return JSON.parse(localStorage.getItem(LS_USER) || "null"); }
    catch { return null; }
  }
  function getEmail() {
    const u = getUser();
    return (u?.correo || "").toLowerCase();
  }

  // 🔐 Login REAL: correo + password
  async function login(correo, password) {
    const S = window.PRESTALAB?.SERVICES || {};
    const payload = { correo, password };

    // Ajusta el endpoint si tu servicio difiere (p.ej. "/auth/login")
    const res = await window.API.post(S.AUTH, "/auth/login", payload, { auth: false });

    // Esperamos { token, usuario?: { ... } } o similar
    if (!res || !res.token) throw new Error("Respuesta de login inválida");

    // Si el backend devuelve datos del usuario, guárdalos. Si no, al menos el correo.
    const user = res.usuario || { correo };
    saveSession(res.token, user);
    return res;
  }

  function logout() {
    clearSession();
    location.href = "index.html";
  }
  function requireAuth() {
    if (!getToken()) location.href = "index.html";
  }

  window.Auth = { login, logout, getToken, getUser, getEmail, requireAuth };
  console.log("[AUTH] Listo · sesión por correo + password");
})();
