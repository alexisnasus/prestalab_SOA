// mis-solicitudes.js — Listar solicitudes del usuario (PRART) con control de admin (CORREGIDO)
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const results = document.getElementById("solWrap");
  const state = document.getElementById("state");
  const AUTH_SERVICE = S.AUTH || 'regist'; // Servicio para actualizar estado
  const CATALOG_SERVICE = S.CATALOG || 'prart'; // Servicio para listar

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
      try {
        pre.textContent =
          typeof extra === "string" ? extra : JSON.stringify(extra, null, 2);
      } catch {
        pre.textContent = String(extra);
      }
      state.appendChild(pre);
    }
    state.style.display = "block";
    state.style.borderColor = ok ? "rgba(34,197,94,0.35)" : "rgba(239,68,68,0.35)";
    state.style.color = ok ? "#22c55e" : "#ef4444";
    state.style.background = ok ? "rgba(34,197,94,0.08)" : "rgba(239,68,68,0.08)";
  };
  const clearBanner = () => { state.style.display = "none"; };
  const setLoading = (on = true) => { if (on) results.innerHTML = '<p style="opacity:.7">Cargando…</p>'; };

  // ---------- ADMIN ----------
  const isAdmin = (() => {
    const correo = window.Auth?.getEmail?.() || "";
    const admins = window.PRESTALAB?.ADMIN_EMAILS || ["admin.prestalab@udp.cl"];
    return admins.includes(correo);
  })();

  // --- FUNCIÓN DE APROBAR CORREGIDA ---
  async function aprobarSolicitud(id) {
    if (!confirm(`¿Aprobar la solicitud #${id}?`)) return;
    try {
      // LLAMAMOS AL SERVICIO CORRECTO (regist) PARA CAMBIAR EL ESTADO
      await API.put(AUTH_SERVICE, `/solicitudes/${id}/actualizar`, { estado: "APROBADA" }, { auth: true });
      setBanner(`Solicitud #${id} aprobada.`, true);
      await buscarSolicitudes(); // Recargar la lista
    } catch (e) {
      setBanner(`Error al aprobar la solicitud #${id}: ${e?.payload?.detail || e.message}`, false, e.payload);
    }
  }

  // --- FUNCIÓN DE RECHAZAR CORREGIDA ---
  async function rechazarSolicitud(id) {
    if (!confirm(`¿Rechazar la solicitud #${id}?`)) return;
    try {
      // LLAMAMOS AL SERVICIO CORRECTO (regist) PARA CAMBIAR EL ESTADO
      await API.put(AUTH_SERVICE, `/solicitudes/${id}/actualizar`, { estado: "RECHAZADA" }, { auth: true });
      setBanner(`Solicitud #${id} rechazada.`, true);
      await buscarSolicitudes(); // Recargar la lista
    } catch (e) {
      setBanner(`Error al rechazar la solicitud #${id}: ${e?.payload?.detail || e.message}`, false, e.payload);
    }
  }

  // ---------- RENDER ----------
  function render(list) {
    // ... (El código de render no necesita cambios, se mantiene igual)
    results.innerHTML = "";
    const items = Array.isArray(list) ? list : [];

    if (!items.length) {
      results.innerHTML = '<p style="opacity:.8">No tienes solicitudes registradas.</p>';
      return;
    }

    const grid = document.createElement("div");
    grid.className = "sol-grid";

    items.forEach((s) => {
      const itemName = s.articulo_nombre ?? s.item_nombre ?? (Array.isArray(s.items) && s.items[0]?.nombre) ?? "—";
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

      if (isAdmin && String(s.estado).toUpperCase() === "PENDIENTE") {
        const actions = document.createElement("div");
        actions.className = "sol-actions";
        actions.innerHTML = `
          <button class="btn btn-small btn-success" data-approve="${s.id}">Aprobar</button>
          <button class="btn btn-small btn-danger" data-reject="${s.id}">Rechazar</button>
        `;
        card.appendChild(actions);

        actions.querySelector("[data-approve]")?.addEventListener("click", (ev) => {
          ev.preventDefault();
          const id = ev.currentTarget.getAttribute("data-approve");
          aprobarSolicitud(id);
        });
        actions.querySelector("[data-reject]")?.addEventListener("click", (ev) => {
          ev.preventDefault();
          const id = ev.currentTarget.getAttribute("data-reject");
          rechazarSolicitud(id);
        });
      }
      grid.appendChild(card);
    });
    results.appendChild(grid);
  }

  // ---------- FLUJO PRINCIPAL Y HELPERS (sin cambios) ----------
  function normalizeSolicitudes(resp) { /* ...código sin cambios... */ }
  async function fetchSolicitudes({ uid, correo }) { /* ...código sin cambios... */ }
  async function resolveUserIdByCorreo(correo) { /* ...código sin cambios... */ }
  async function buscarSolicitudes() { /* ...código sin cambios... */ }

  // ... (Pega aquí las funciones sin cambios de tu archivo original)
  function normalizeSolicitudes(resp) {
    const body = resp && typeof resp === "object" && "data" in resp ? resp.data : resp;
    if (Array.isArray(body)) return body;
    if (Array.isArray(body?.solicitudes)) return body.solicitudes;
    if (Array.isArray(body?.data)) return body.data;
    return [];
  }

  async function fetchSolicitudes({ uid, correo }) {
    const params = new URLSearchParams();
    if (uid && /^\d+$/.test(String(uid))) params.set("usuario_id", String(uid));
    if (correo) params.set("correo", correo); // Corregido para enviar siempre el correo
    const endpoint = `/solicitudes?${params.toString()}`;
    const resp = await API.get(CATALOG_SERVICE, endpoint, { auth: true });
    return { endpoint, resp, solicitudes: normalizeSolicitudes(resp.solicitudes) };
  }

  async function resolveUserIdByCorreo(correo) {
    try {
      const r = await API.get(AUTH_SERVICE, `/usuarios?correo=${encodeURIComponent(correo)}`, { auth: true });
      const body = r && typeof r === "object" && "data" in r ? r.data : r;
      if (Array.isArray(body) && body[0]?.id) return body[0].id;
      if (body?.id) return body.id;
    } catch (_) {}
    const legacy = localStorage.getItem("pl_user_id");
    if (legacy && /^\d+$/.test(legacy)) return Number(legacy);
    return null;
  }

  async function buscarSolicitudes() {
    clearBanner();
    setLoading(true);

    const correo = window.Auth?.getEmail?.();
    if (!correo) {
      setBanner("No hay sesión activa.", false);
      setLoading(false);
      return;
    }

    let uid = localStorage.getItem("pl_user_id");
    if (!uid) {
        uid = await resolveUserIdByCorreo(correo);
    }
    
    try {
      let { solicitudes } = await fetchSolicitudes({ uid, correo });
      render(solicitudes);
      setBanner(`Solicitudes cargadas (${solicitudes.length})`, true);
    } catch (e) {
      setBanner("No se pudieron obtener tus solicitudes.", false, e.payload);
    } finally {
      setLoading(false);
    }
  }

  // ---------- INIT ----------
  (function init() {
    window.Auth?.requireAuth?.();
    const user = window.Auth?.getUser?.();
    document.getElementById("userBadge").textContent = user?.correo || "Usuario";
    document.getElementById("btnLogout").addEventListener("click", () => window.Auth.logout());
    buscarSolicitudes();
  })();
})();