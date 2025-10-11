// mis-solicitudes.js — Vista funcional para listar solicitudes desde PRART
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const results = document.getElementById("solWrap");
  const state = document.getElementById("state");

  // ---- utilitarios UI ----
  const show = (msg, ok = false, extra = null) => {
    state.innerHTML = "";
    const msgDiv = document.createElement("div");
    msgDiv.textContent = msg;
    state.appendChild(msgDiv);

    if (extra) {
      const pre = document.createElement("pre");
      pre.textContent =
        typeof extra === "string" ? extra : JSON.stringify(extra, null, 2);
      pre.style.whiteSpace = "pre-wrap";
      pre.style.marginTop = "6px";
      state.appendChild(pre);
    }

    state.style.display = "block";
    state.style.borderColor = ok ? "rgba(34,197,94,0.35)" : "rgba(239,68,68,0.35)";
    state.style.color = ok ? "#22c55e" : "#ef4444";
    state.style.background = ok
      ? "rgba(34,197,94,0.08)"
      : "rgba(239,68,68,0.08)";
  };

  const clear = () => (state.style.display = "none");

  // ---- render ----
  const render = (list) => {
    results.innerHTML = "";
    if (!list?.length) {
      results.innerHTML =
        '<p style="opacity:.8">No tienes solicitudes registradas.</p>';
      return;
    }

    // Creamos tabla para mostrar las solicitudes
    const table = document.createElement("table");
    table.className = "sol-table";
    table.innerHTML = `
      <thead>
        <tr>
          <th>ID</th>
          <th>Tipo</th>
          <th>Estado</th>
          <th>Artículo</th>
          <th>Fecha</th>
        </tr>
      </thead>
      <tbody></tbody>
    `;
    const tbody = table.querySelector("tbody");

    list.forEach((s) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${s.id ?? "—"}</td>
        <td>${s.tipo ?? "—"}</td>
        <td>${s.estado ?? "—"}</td>
        <td>${s.articulo_nombre ?? "—"}</td>
        <td>${s.registro_instante ?? "—"}</td>
      `;
      tbody.appendChild(tr);
    });

    results.appendChild(table);
  };

  // ---- fetch principal ----
  async function buscarSolicitudes() {
    clear();

    const correo = window.Auth?.getEmail?.();
    if (!correo) {
      show("No hay sesión activa.", false);
      return;
    }

    // ID opcional por compatibilidad
    const usuario_id = localStorage.getItem("pl_user_id") || "";
    const endpoint = `/solicitudes?usuario_id=${encodeURIComponent(
      usuario_id
    )}&correo=${encodeURIComponent(correo)}`;

    try {
      console.log("[PRART] GET", endpoint);
      const data = await API.get(S.CATALOG, endpoint, { auth: true });

      // Determinar si el backend devuelve un array directo o envuelto
      const solicitudes = Array.isArray(data)
        ? data
        : data?.data || data?.solicitudes || [];

      render(solicitudes);
      show(`Solicitudes cargadas correctamente (${solicitudes.length})`, true);
    } catch (e) {
      console.error("[MisSolicitudes] Error obteniendo solicitudes", e);
      let msg = "No se pudieron obtener tus solicitudes.";

      if (e?.status === 405) {
        msg =
          "El servicio aún no permite GET /solicitudes. Verifica que el backend esté actualizado.";
      } else if (e?.payload?.detail || e?.payload?.message || e?.payload?.error) {
        msg = e.payload.detail || e.payload.message || e.payload.error;
      }

      const extra = {
        status: e?.status ?? null,
        raw: e?.payload ?? null,
        endpoint,
      };
      show(msg, false, extra);
    }
  }

  // ---- inicio ----
  window.Auth?.requireAuth?.();
  const user = window.Auth?.getUser?.();
  document.getElementById("userBadge").textContent = user?.correo || "Usuario";
  document
    .getElementById("btnLogout")
    .addEventListener("click", () => window.Auth.logout());

  buscarSolicitudes();
})();
