// mis-solicitudes.js — (CORREGIDO PARA NUEVA API)
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const results = document.getElementById("solWrap");
  const state = document.getElementById("state");
  const AUTH_SERVICE = S.AUTH || 'regist'; // Servicio para actualizar estado
  const CATALOG_SERVICE = S.CATALOG || 'prart'; // Servicio para listar

  // ---------- UI (Sin cambios) ----------
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

  // ---------- ADMIN (Sin cambios) ----------
  const isAdmin = (() => {
    const correo = window.Auth?.getEmail?.() || "";
    const admins = window.PRESTALAB?.ADMIN_EMAILS || ["admin.prestalab@udp.cl"];
    return admins.includes(correo);
  })();

  // --- FUNCIÓN DE APROBAR (CORREGIDA) ---
  async function aprobarSolicitud(id) {
    if (!confirm(`¿Aprobar la solicitud #${id}?`)) return;
    try {
      // ANTES: await API.put(AUTH_SERVICE, `/solicitudes/${id}/actualizar`, ...);
      // AHORA:
      // Esta operación está en el servicio 'regist'
      const payload = { solicitud_id: Number(id), estado: "APROBADA" };
      await API.updateSolicitud(payload);
      
      setBanner(`Solicitud #${id} aprobada.`, true);
      await buscarSolicitudes(); // Recargar la lista
    } catch (e) {
      setBanner(`Error al aprobar la solicitud #${id}: ${e?.payload?.detail || e.message}`, false, e.payload);
    }
  }

  // --- FUNCIÓN DE RECHAZAR (CORREGIDA) ---
  async function rechazarSolicitud(id) {
    if (!confirm(`¿Rechazar la solicitud #${id}?`)) return;
    try {
      // ANTES: await API.put(AUTH_SERVICE, `/solicitudes/${id}/actualizar`, ...);
      // AHORA:
      // Esta operación está en el servicio 'regist'
      const payload = { solicitud_id: Number(id), estado: "RECHAZADA" };
      await API.updateSolicitud(payload);
      
      setBanner(`Solicitud #${id} rechazada.`, true);
      await buscarSolicitudes(); // Recargar la lista
    } catch (e) {
      setBanner(`Error al rechazar la solicitud #${id}: ${e?.payload?.detail || e.message}`, false, e.payload);
    }
  }

  // ---------- RENDER (Sin cambios) ----------
  // Tu función de renderizado ya funciona con los datos que devuelve prart/app.py
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
      // prart/app.py get_solicitudes devuelve 'items'
      const itemName = (Array.isArray(s.items) && s.items[0]?.nombre) ?? s.articulo_nombre ?? s.item_nombre ?? "—";
      const card = document.createElement("article");
      card.className = "sol-card";
      card.innerHTML = `
        <div class="sol-top">
          <span class="sol-id">#${s.id ?? "—"}</span>
          <span class="sol-badge ${String(s.estado || "").toLowerCase()}">${s.estado ?? "—"}</span>
        </div>
        <h3 class="sol-title">${s.tipo ?? "—"}</h3>
        <p class="sol-item"><strong>Ítem(s):</strong> ${itemName}</p>
        <p class="sol-date"><strong>Fecha:</strong> ${new Date(s.registro_instante).toLocaleString() ?? s.creada_en ?? "—"}</p>
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

  // ---------- FLUJO PRINCIPAL Y HELPERS (CORREGIDOS) ----------
  
  function normalizeSolicitudes(resp) {
    // prart/app.py devuelve { "solicitudes": [...] }
    const body = resp && typeof resp === "object" ? resp : {};
    if (Array.isArray(body?.solicitudes)) return body.solicitudes;
    if (Array.isArray(body)) return body;
    return [];
  }

  // --- CORREGIDO: ahora usa la nueva API ---
  async function fetchSolicitudes({ correo }) {
    // prart/app.py
    // get_solicitudes puede buscar solo por email, así que 'uid' no es necesario.
    const payload = { correo: correo };
    
    // ANTES: const resp = await API.get(CATALOG_SERVICE, endpoint, { auth: true });
    // AHORA:
    const resp = await API.getSolicitudes(payload);
    
    return { solicitudes: normalizeSolicitudes(resp) };
  }

  // --- ELIMINADO: `resolveUserIdByCorreo` ya no es necesario ---

  // --- CORREGIDO: Lógica simplificada ---
  async function buscarSolicitudes() {
    clearBanner();
    setLoading(true);

    const correo = window.Auth?.getEmail?.();
    if (!correo) {
      setBanner("No hay sesión activa.", false);
      setLoading(false);
      return;
    }
    
    try {
      // Ya no necesitamos 'uid', solo pasamos el correo
      let { solicitudes } = await fetchSolicitudes({ correo });
      render(solicitudes);
      setBanner(`Solicitudes cargadas (${solicitudes.length})`, true);
    } catch (e) {
      setBanner("No se pudieron obtener tus solicitudes.", false, e.payload);
    } finally {
      setLoading(false);
    }
  }

  // ---------- INIT (Sin cambios) ----------
  (function init() {
    window.Auth?.requireAuth?.();
    const user = window.Auth?.getUser?.();
    document.getElementById("userBadge").textContent = user?.correo || "Usuario";
    document.getElementById("btnLogout").addEventListener("click", () => window.Auth.logout());
    buscarSolicitudes();
  })();
})();