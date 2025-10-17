// mis-solicitudes.js — Listar solicitudes del usuario (PRART) con control de admin
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const results = document.getElementById("solWrap");
  const state = document.getElementById("state");

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
    state.style.borderColor = ok
      ? "rgba(34,197,94,0.35)"
      : "rgba(239,68,68,0.35)";
    state.style.color = ok ? "#22c55e" : "#ef4444";
    state.style.background = ok
      ? "rgba(34,197,94,0.08)"
      : "rgba(239,68,68,0.08)";
  };
  const clearBanner = () => {
    state.style.display = "none";
  };
  const setLoading = (on = true) => {
    if (on) results.innerHTML = '<p style="opacity:.7">Cargando…</p>';
  };

  // ---------- ADMIN ----------
  const isAdmin = (() => {
    const correo = window.Auth?.getEmail?.() || "";
    const admins = window.PRESTALAB?.ADMIN_EMAILS || [
      "admin.prestalab@udp.cl",
    ];
    return admins.includes(correo);
  })();

  async function aprobarSolicitud(id) {
    try {
      // 1️⃣ Intento principal: crear préstamo
      const payload = { solicitud_id: Number(id) };
      await API.post(S.CATALOG, "/prestamos", payload, { auth: true });
      setBanner(`Solicitud #${id} aprobada como préstamo.`, true);
      await buscarSolicitudes();
    } catch (e) {
      // 2️⃣ Si el endpoint no existe, usamos PUT estado=APROBADA
      if (e?.status === 404 || e?.status === 405) {
        try {
          await API.put(
            S.CATALOG,
            `/solicitudes/${id}/estado`,
            { estado: "APROBADA" },
            { auth: true }
          );
          setBanner(`Solicitud #${id} marcada como APROBADA.`, true);
          await buscarSolicitudes();
          return;
        } catch (e2) {
          setBanner(
            `No se pudo aprobar la solicitud #${id}`,
            false,
            e2?.payload || e2
          );
          return;
        }
      }
      setBanner(
        `No se pudo aprobar la solicitud #${id}`,
        false,
        e?.payload || e
      );
    }
  }

  async function rechazarSolicitud(id) {
    try {
      const motivo = prompt("Motivo de rechazo (opcional):") || null;
      await API.put(
        S.CATALOG,
        `/solicitudes/${id}/estado`,
        { estado: "RECHAZADA", motivo },
        { auth: true }
      );
      setBanner(`Solicitud #${id} rechazada.`, true);
      await buscarSolicitudes();
    } catch (e) {
      setBanner(
        `No se pudo rechazar la solicitud #${id}`,
        false,
        e?.payload || e
      );
    }
  }

  // ---------- RENDER ----------
  function render(list) {
    results.innerHTML = "";
    const items = Array.isArray(list) ? list : [];

    if (!items.length) {
      results.innerHTML =
        '<p style="opacity:.8">No tienes solicitudes registradas.</p>';
      return;
    }

    const grid = document.createElement("div");
    grid.className = "sol-grid";

    items.forEach((s) => {
      const itemName =
        s.articulo_nombre ??
        s.item_nombre ??
        (Array.isArray(s.items) && s.items[0]?.nombre) ??
        "—";

      const card = document.createElement("article");
      card.className = "sol-card";
      card.innerHTML = `
        <div class="sol-top">
          <span class="sol-id">#${s.id ?? "—"}</span>
          <span class="sol-badge ${String(s.estado || "").toLowerCase()}">${
        s.estado ?? "—"
      }</span>
        </div>
        <h3 class="sol-title">${s.tipo ?? "—"}</h3>
        <p class="sol-item"><strong>Artículo:</strong> ${itemName}</p>
        <p class="sol-date"><strong>Fecha:</strong> ${
          s.registro_instante ?? s.creada_en ?? "—"
        }</p>
      `;

      // Solo admin ve acciones si está PENDIENTE
      if (isAdmin && String(s.estado).toUpperCase() === "PENDIENTE") {
        const actions = document.createElement("div");
        actions.className = "sol-actions";
        actions.innerHTML = `
          <button class="btn btn-small btn-success" data-approve="${s.id}">Aprobar</button>
          <button class="btn btn-small btn-danger" data-reject="${s.id}">Rechazar</button>
        `;
        card.appendChild(actions);

        actions
          .querySelector("[data-approve]")
          ?.addEventListener("click", async (ev) => {
            ev.preventDefault();
            const id = ev.currentTarget.getAttribute("data-approve");
            if (confirm(`¿Aprobar solicitud #${id}?`)) await aprobarSolicitud(id);
          });
        actions
          .querySelector("[data-reject]")
          ?.addEventListener("click", async (ev) => {
            ev.preventDefault();
            const id = ev.currentTarget.getAttribute("data-reject");
            if (confirm(`¿Rechazar solicitud #${id}?`)) await rechazarSolicitud(id);
          });
      }

      grid.appendChild(card);
    });

    results.appendChild(grid);
  }

  // ---------- HELPERS ----------
  function normalizeSolicitudes(resp) {
    const body =
      resp && typeof resp === "object" && "data" in resp ? resp.data : resp;
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
    try {
      const r = await API.get(
        S.AUTH,
        `/usuarios?correo=${encodeURIComponent(correo)}`,
        { auth: true }
      );
      const body = r && typeof r === "object" && "data" in r ? r.data : r;
      if (Array.isArray(body) && body[0]?.id) return body[0].id;
      if (body?.id) return body.id;
    } catch (_) {}
    const legacy = localStorage.getItem("pl_user_id");
    if (legacy && /^\d+$/.test(legacy)) return Number(legacy);
    return null;
  }

  // ---------- FLUJO PRINCIPAL ----------
  async function buscarSolicitudes() {
    clearBanner();
    setLoading(true);

    const correo = window.Auth?.getEmail?.();
    if (!correo) {
      setBanner("No hay sesión activa.", false);
      return;
    }

    let uid = null;
    const stored = localStorage.getItem("pl_user_id");
    if (stored && /^\d+$/.test(stored)) uid = Number(stored);

    try {
      let { endpoint, resp, solicitudes } = await fetchSolicitudes({
        uid,
        correo,
      });

      if (!solicitudes.length && !uid) {
        uid = await resolveUserIdByCorreo(correo);
        if (uid) {
          ({ endpoint, resp, solicitudes } = await fetchSolicitudes({
            uid,
            correo,
          }));
          try {
            localStorage.setItem("pl_user_id", String(uid));
          } catch {}
        }
      }

      render(solicitudes);
      setBanner(
        `Solicitudes cargadas correctamente (${solicitudes.length})`,
        true
      );
    } catch (e) {
      let msg = "No se pudieron obtener tus solicitudes.";
      if (e?.status === 405)
        msg = "El servicio aún no permite GET /solicitudes. Verifica backend.";
      else if (e?.status === 422)
        msg = "El backend rechazó los parámetros. Si usas ID, debe ser numérico.";
      else if (e?.payload?.detail || e?.payload?.message || e?.payload?.error) {
        msg = e.payload.detail || e.payload.message || e.payload.error;
      }
      setBanner(msg, false, { status: e?.status ?? null, raw: e?.payload ?? null });
    }
  }

  // ---------- INIT ----------
  window.Auth?.requireAuth?.();
  const user = window.Auth?.getUser?.();
  document.getElementById("userBadge").textContent = user?.correo || "Usuario";
  document
    .getElementById("btnLogout")
    .addEventListener("click", () => window.Auth.logout());

  buscarSolicitudes();

  
})();
