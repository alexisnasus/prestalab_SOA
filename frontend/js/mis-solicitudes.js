// mis-solicitudes.js — Listar solicitudes del usuario (PRART) con fallback de ID por correo
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const results = document.getElementById("solWrap");
  const state   = document.getElementById("state");

  // ---------- UI ----------
  const setBanner = (msg, ok = false, extra = null) => {
    state.innerHTML = "";
    const p = document.createElement("div");
    p.textContent = String(msg);
    state.appendChild(p);
    if (extra) {
      const pre = document.createElement("pre");
      pre.style.whiteSpace = "pre-wrap";
      pre.style.marginTop = "6px";
      try { pre.textContent = typeof extra === "string" ? extra : JSON.stringify(extra, null, 2); }
      catch { pre.textContent = String(extra); }
      state.appendChild(pre);
    }
    state.style.display   = "block";
    state.style.borderColor = ok ? "rgba(34,197,94,0.35)" : "rgba(239,68,68,0.35)";
    state.style.color       = ok ? "#22c55e"              : "#ef4444";
    state.style.background  = ok ? "rgba(34,197,94,0.08)" : "rgba(239,68,68,0.08)";
  };
  const clearBanner = () => { state.style.display = "none"; };
  const setLoading  = (on = true) => { if (on) results.innerHTML = '<p style="opacity:.7">Cargando…</p>'; };

  // ---------- render ----------
  function render(list) {
    results.innerHTML = "";
    const items = Array.isArray(list) ? list : [];
    if (!items.length) {
      results.innerHTML = '<p style="opacity:.8">No tienes solicitudes registradas.</p>';
      return;
    }
    const grid = document.createElement("div");
    grid.className = "sol-grid";
    items.forEach((s) => {
      const itemName =
        s.articulo_nombre ??
        s.item_nombre ??
        (Array.isArray(s.items) && s.items[0]?.nombre) ?? "—";
      const card = document.createElement("article");
      card.className = "sol-card";
      card.innerHTML = `
        <div class="sol-top">
          <span class="sol-id">#${s.id ?? "—"}</span>
          <span class="sol-badge ${String(s.estado || "").toLowerCase()}">${s.estado ?? "—"}</span>
        </div>
        <h3 class="sol-title">${s.tipo ?? "—"}</h3>
        <p class="sol-item"><strong>Artículo:</strong> ${itemName}</p>
        <p class="sol-date"><strong>Fecha:</strong> ${s.registro_instante ?? s.creada_en ?? "—"}</p>
      `;
      grid.appendChild(card);
    });
    results.appendChild(grid);
  }

  // ---------- helpers ----------
  function normalizeSolicitudes(resp) {
    // resp puede ser:
    // 1) { success, data: { usuario_id, total, solicitudes:[...] } }
    // 2) { solicitudes:[...] }
    // 3) [ ... ]
    const body = (resp && typeof resp === "object" && "data" in resp) ? resp.data : resp;
    if (Array.isArray(body)) return body;
    if (Array.isArray(body?.solicitudes)) return body.solicitudes;
    if (Array.isArray(body?.data)) return body.data;
    return [];
  }

  async function fetchSolicitudes({ uid, correo }) {
    const params = new URLSearchParams();
    if (uid && /^\d+$/.test(String(uid))) params.set("usuario_id", String(uid));
    params.set("correo", correo);
    const endpoint = `/solicitudes?${params.toString()}`;
    const resp = await API.get(S.CATALOG, endpoint, { auth: true });
    return { endpoint, resp, solicitudes: normalizeSolicitudes(resp) };
  }

  async function resolveUserIdByCorreo(correo) {
    // Intento 1: si el bus/REGIST soporta ?correo
    try {
      const r = await API.get(S.AUTH, `/usuarios?correo=${encodeURIComponent(correo)}`, { auth: true });
      const body = (r && typeof r === "object" && "data" in r) ? r.data : r;
      if (Array.isArray(body) && body[0]?.id) return body[0].id;
      if (body?.id) return body.id;
    } catch (_) {}
    // Intento 2: usar lo que haya en localStorage si es numérico
    const legacy = localStorage.getItem("pl_user_id");
    if (legacy && /^\d+$/.test(legacy)) return Number(legacy);
    return null;
  }

  // ---------- flujo principal ----------
  async function buscarSolicitudes() {
    clearBanner();
    setLoading(true);

    const correo = window.Auth?.getEmail?.();
    if (!correo) {
      setBanner("No hay sesión activa.", false);
      return;
    }

    // 1) primero probamos con lo que tengamos (correo + uid si existe)
    let uid = null;
    const stored = localStorage.getItem("pl_user_id");
    if (stored && /^\d+$/.test(stored)) uid = Number(stored);

    try {
      let { endpoint, resp, solicitudes } = await fetchSolicitudes({ uid, correo });

      // 2) si vino vacío y no teníamos uid, resolvemos id por correo y reintentamos
      if (!solicitudes.length && !uid) {
        uid = await resolveUserIdByCorreo(correo);
        if (uid) {
          ({ endpoint, resp, solicitudes } = await fetchSolicitudes({ uid, correo }));
          // guardamos para próximas veces
          try { localStorage.setItem("pl_user_id", String(uid)); } catch {}
        }
      }

      render(solicitudes);
      setBanner(`Solicitudes cargadas correctamente (${solicitudes.length})`, true);
    } catch (e) {
      let msg = "No se pudieron obtener tus solicitudes.";
      if (e?.status === 405) msg = "El servicio aún no permite GET /solicitudes. Verifica backend y Bus.";
      else if (e?.status === 422) msg = "El backend rechazó los parámetros. Si usas ID, debe ser numérico.";
      else if (e?.payload?.detail || e?.payload?.message || e?.payload?.error) {
        msg = e.payload.detail || e.payload.message || e.payload.error;
      }
      setBanner(msg, false, { status: e?.status ?? null, raw: e?.payload ?? null });
    }
  }

  // ---------- init ----------
  window.Auth?.requireAuth?.();
  const user = window.Auth?.getUser?.();
  document.getElementById("userBadge").textContent = user?.correo || "Usuario";
  document.getElementById("btnLogout").addEventListener("click", () => window.Auth.logout());
  buscarSolicitudes();
})();
