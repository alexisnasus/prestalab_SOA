// auth.js - Sesión + resolución automática de ID de usuario
(function () {
  const LS_TOKEN = "pl_token";
  const LS_USER  = "pl_user";
  const LS_UID   = "pl_user_id";

  function saveSession(token, user) {
    localStorage.setItem(LS_TOKEN, token);
    localStorage.setItem(LS_USER, JSON.stringify(user || null));
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
  function setUserId(id) {
    if (id && /^\d+$/.test(String(id))) {
      localStorage.setItem(LS_UID, String(id));
      return Number(id);
    }
    return null;
  }
  function getUserId() {
    const v = localStorage.getItem(LS_UID);
    return v && /^\d+$/.test(v) ? Number(v) : null;
  }

  // --- Resolver ID preguntando al servicio de usuarios (regist) por correo
// --- Dentro de auth.js ---
async function resolveUserIdByEmail(correo) {
  const S = window.PRESTALAB?.SERVICES || {};
  if (!S.AUTH || !correo) return null;
  const email = correo.toLowerCase();
  const enc = encodeURIComponent(email);

  // 1) GET candidatos (algunas APIs lo permiten)
  const getAttempts = [
    [`/usuarios?correo=${enc}`, true],
    [`/usuarios?correo=${enc}`, false],
    ['/usuarios', true],
    ['/usuarios', false],
    ['/usuario', true],
    ['/usuario', false],
    [`/usuario/${enc}`, true],
    [`/usuario/${enc}`, false],
  ];

  // 2) POST candidatos (muchos servicios exponen "search/find/by_email")
  const postAttempts = [
    ['/usuarios/search', { correo: email }],
    ['/usuarios/find',   { correo: email }],
    ['/usuarios/by_email', { correo: email }],
    ['/usuarios/email',  { correo: email }],
    // fallback genérico: algunas APIs aceptan POST /usuarios con filtro
    ['/usuarios',        { correo: email }],
    // variantes en singular
    ['/usuario/search',  { correo: email }],
    ['/usuario/find',    { correo: email }],
    ['/usuario/by_email',{ correo: email }],
    ['/usuario/email',   { correo: email }],
  ];

  const pickUser = (data) => {
    if (!data) return null;
    if (Array.isArray(data)) {
      return data.find(x => (x?.correo || '').toLowerCase() === email) || null;
    }
    if (typeof data === 'object') {
      // estructuras comunes
      const pools = [data.data, data.items, data.results, data.usuarios, data.users];
      for (const arr of pools) {
        if (Array.isArray(arr)) {
          const u = arr.find(x => (x?.correo || '').toLowerCase() === email);
          if (u) return u;
        }
      }
      if (data.correo && (data.correo || '').toLowerCase() === email) return data;
      if (data.usuario && (data.usuario.correo || '').toLowerCase() === email) return data.usuario;
    }
    return null;
  };

  // GETs (bus -> siempre POST /route, pero method interno GET)
  for (const [ep, useAuth] of getAttempts) {
    try {
      const out = await window.API.get(S.AUTH, ep, { auth: !!useAuth });
      const u = pickUser(out);
      if (u?.id) return setUserId(u.id);
    } catch {}
  }

  // POSTs con body { correo }
  for (const [ep, body] of postAttempts) {
    for (const useAuth of [true, false]) {
      try {
        const out = await window.API.post(S.AUTH, ep, body, { auth: useAuth });
        const u = pickUser(out);
        if (u?.id) return setUserId(u.id);
      } catch {}
    }
  }

  return null;
}


  // --- API pública para asegurar que el ID esté disponible
  async function ensureUserId() {
    const cached = getUserId();
    if (cached) return cached;
    const correo = (getUser()?.correo || '').toLowerCase();
    const resolved = await resolveUserIdByEmail(correo);
    return resolved || null;
  }

  // El backend valida { correo, password: "mock_password" } y devuelve { token }
  async function login(correo, password) {
    const S = window.PRESTALAB?.SERVICES || {};
    const body = { correo, email: correo, password }; // compat
    const res = await window.API.post(S.AUTH, "/auth/login", body, { auth: false });
    if (!res || !res.token) throw new Error("Respuesta de login inválida");

    // Guardar token + correo
    saveSession(res.token, { correo });

    // Resolver y cachear ID de usuario (no bloqueante si falla)
    try { await ensureUserId(); } catch (_) {}

    return res;
  }

  function logout() { clearSession(); location.href = "index.html"; }
  function requireAuth() { if (!getToken()) location.href = "index.html"; }
// --- Resolver y cachear el ID de usuario por correo (vía servicio REGIST) ---
async function ensureUserId() {
  const LS_UID = 'pl_user_id';

  // 0) Si ya está cacheado, úsalo
  const saved = localStorage.getItem(LS_UID);
  if (saved && /^\d+$/.test(saved)) return Number(saved);

  const S = window.PRESTALAB?.SERVICES || {};
  const email = (getUser()?.correo || '').toLowerCase();
  if (!email) return null;

  // Intentos de endpoints típicos
  const enc = encodeURIComponent(email);
  const candidates = [
    `/usuarios?correo=${enc}`,
    `/usuario?correo=${enc}`,
    `/usuarios/by_email/${enc}`,
    `/usuarios/email/${enc}`,
    `/usuarios`,
    `/usuario`,
  ];

  // Cómo extraer el id de varias formas de respuesta
  const pickId = (data) => {
    if (!data) return null;
    if (Array.isArray(data)) {
      const row = data.find(x => (x.correo || x.email || '').toLowerCase() === email);
      return row?.id ?? null;
    }
    if (typeof data === 'object') {
      if (data.usuario?.id) return data.usuario.id;
      if (data.id) return data.id;
    }
    return null;
  };

  for (const ep of candidates) {
    try {
      const res = await window.API.get(S.AUTH, ep, { auth: true });
      const id = pickId(res);
      if (id) {
        localStorage.setItem(LS_UID, String(id));
        return id;
      }
    } catch {
      // probar siguiente
    }
  }
  return null;
}

window.Auth = { login, logout, getToken, getUser, requireAuth, ensureUserId };
console.log("[AUTH] Utilidades listas (modo correo + token)");

})();
