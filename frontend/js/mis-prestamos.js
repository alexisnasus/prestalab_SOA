// mis-prestamos.js — Ver, cancelar, renovar y devolver préstamos
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const results = document.getElementById("prestamosWrap");
  const state = document.getElementById("state");

  const setBanner = (msg, ok = false, extra = null) => {
    state.innerHTML = "";
    const p = document.createElement("div");
    p.textContent = msg;
    state.appendChild(p);
    if (extra) {
      const pre = document.createElement("pre");
      pre.textContent = JSON.stringify(extra, null, 2);
      pre.style.whiteSpace = "pre-wrap";
      pre.style.marginTop = "6px";
      state.appendChild(pre);
    }
    state.style.display = "block";
    state.style.borderColor = ok ? "rgba(34,197,94,0.35)" : "rgba(239,68,68,0.35)";
    state.style.color = ok ? "#22c55e" : "#ef4444";
    state.style.background = ok ? "rgba(34,197,94,0.08)" : "rgba(239,68,68,0.08)";
  };

  const clearBanner = () => state.style.display = "none";
  const setLoading = (on = true) => { results.innerHTML = on ? "<p>Cargando…</p>" : ""; };

  // ---------- render ----------
  function renderPrestamos(list) {
    results.innerHTML = "";
    if (!list?.length) {
      results.innerHTML = '<p style="opacity:.8">No tienes préstamos activos.</p>';
      return;
    }

    const grid = document.createElement("div");
    grid.className = "sol-grid";

    list.forEach((p) => {
      const itemName = p.item_nombre ?? p.articulo_nombre ?? "Artículo no especificado";
      const card = document.createElement("article");
      card.className = "sol-card";

      card.innerHTML = `
        <div class="sol-top">
          <span class="sol-id">#${p.id}</span>
          <span class="sol-badge ${String(p.estado || "").toLowerCase()}">${p.estado ?? "—"}</span>
        </div>
        <h3 class="sol-title">${p.tipo ?? "PRÉSTAMO"}</h3>
        <p class="sol-item"><strong>Artículo:</strong> ${itemName}</p>
        <p class="sol-date"><strong>Fecha:</strong> ${p.registro_instante ?? "—"}</p>
        <div class="sol-actions">
          ${p.estado === "PENDIENTE" ? `<button class="btn-cancelar" data-id="${p.id}">Cancelar</button>` : ""}
          ${p.estado === "APROBADA" ? `
            <button class="btn-renovar" data-id="${p.id}">Renovar</button>
            <button class="btn-devolver" data-id="${p.id}">Devolver</button>
          ` : ""}
        </div>
      `;
      grid.appendChild(card);
    });

    results.appendChild(grid);

    // Wire buttons
    results.querySelectorAll(".btn-cancelar").forEach(b =>
      b.addEventListener("click", () => handleAccion("cancelar", b.dataset.id))
    );
    results.querySelectorAll(".btn-renovar").forEach(b =>
      b.addEventListener("click", () => handleAccion("renovar", b.dataset.id))
    );
    results.querySelectorAll(".btn-devolver").forEach(b =>
      b.addEventListener("click", () => handleAccion("devolver", b.dataset.id))
    );
  }

  // ---------- acciones ----------
  async function handleAccion(tipo, id) {
    try {
      let method, endpoint, payload = null;

      if (tipo === "cancelar") {
        method = "DELETE";
        endpoint = `/reservas/${id}`;
      } else if (tipo === "renovar") {
        method = "PUT";
        endpoint = `/prestamos/${id}/renovar`;
      } else if (tipo === "devolver") {
        method = "POST";
        endpoint = `/devoluciones`;
        payload = { prestamo_id: Number(id) };
      }

      const res = await API.send(S.CATALOG, method, endpoint, payload, { auth: true });
      setBanner(`Acción "${tipo}" ejecutada correctamente.`, true, res);
      await cargarPrestamos(); // refresca lista
    } catch (e) {
      console.error("[PRESTAMOS] Acción fallida", e);
      setBanner(`Error ejecutando "${tipo}"`, false, e);
    }
  }

  // ---------- fetch ----------
  async function cargarPrestamos() {
    clearBanner(); setLoading(true);

    const correo = window.Auth?.getEmail?.();
    if (!correo) { setBanner("No hay sesión activa.", false); return; }

    try {
      const data = await API.get(S.CATALOG, `/solicitudes?correo=${encodeURIComponent(correo)}`, { auth: true });
      const list = Array.isArray(data?.data?.solicitudes) ? data.data.solicitudes : [];
      renderPrestamos(list);
      setBanner(`Préstamos cargados (${list.length})`, true);
    } catch (e) {
      console.error("[PRESTAMOS] Error obteniendo préstamos", e);
      setBanner("No se pudieron obtener tus préstamos.", false, e);
    } finally {
      setLoading(false);
    }
  }

  // ---------- init ----------
  window.Auth?.requireAuth?.();
  const user = window.Auth?.getUser?.();
  document.getElementById("userBadge").textContent = user?.correo || "Usuario";
  document.getElementById("btnLogout").addEventListener("click", () => window.Auth.logout());
  cargarPrestamos();

  
})();
