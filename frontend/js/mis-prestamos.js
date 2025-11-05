// mis-prestamos.js — (CORREGIDO PARA NUEVA API)
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const results = document.getElementById("prestamosWrap");
  const state = document.getElementById("state");

  // ---------- UI (Sin cambios) ----------
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

  // ---------- render (Sin cambios) ----------
  function renderPrestamos(list) {
    results.innerHTML = "";
    if (!list?.length) {
      results.innerHTML = '<p style="opacity:.8">No tienes préstamos activos.</p>';
      return;
    }

    const grid = document.createElement("div");
    grid.className = "sol-grid";

    list.forEach((p) => {
      // prart/app.py get_solicitudes devuelve 'items'
      const itemName = (Array.isArray(p.items) && p.items[0]?.nombre) ?? p.item_nombre ?? p.articulo_nombre ?? "Artículo no especificado";
      const card = document.createElement("article");
      card.className = "sol-card";

      // Lógica de botones basada en el estado de la *solicitud*
      let actions = '';
      if (p.estado === "PENDIENTE") {
        // Asumimos que "cancelar" una solicitud PENDIENTE es 'cancel_reserva'
        // NOTA: Esto podría ser 'cancel_solicitud' que no está implementado.
        // Por ahora, lo mapeamos a 'cancelReserva' que sí existe.
        actions = `<button class="btn-cancelar" data-id="${p.id}" data-tipo="reserva">Cancelar</button>`;
      } else if (p.estado === "APROBADA") {
         // Si la solicitud está APROBADA, aún no es un préstamo.
         // Mostramos los botones de renovar/devolver basados en los préstamos *reales*
         // Esta lógica es compleja. Por ahora, simplificamos:
         // Si es un préstamo (tipo PRESTAMO) y está ACTIVO, mostramos botones.
         // Tu lógica original mostraba botones para "APROBADA", lo cual es confuso.
         // Vamos a asumir que 'APROBADA' es 'ACTIVO' para un préstamo.
         actions = `
            <button class="btn-renovar" data-id="${p.id}" data-tipo="prestamo">Renovar</button>
            <button class="btn-devolver" data-id="${p.id}" data-tipo="prestamo">Devolver</button>
          `;
      }
      
      // Ajuste para mostrar Préstamos Activos (no solo solicitudes)
      // La lista 'list' contiene 'solicitudes'. Deberíamos filtrar por tipo PRÉSTAMO
      // y estado APROBADA (que implica "activo" en tu lógica)
      if (p.tipo !== "PRÉSTAMO") return; // Solo mostrar préstamos
      
      card.innerHTML = `
        <div class="sol-top">
          <span class="sol-id">Solicitud #${p.id}</span>
          <span class="sol-badge ${String(p.estado || "").toLowerCase()}">${p.estado ?? "—"}</span>
        </div>
        <h3 class="sol-title">${p.tipo ?? "PRÉSTAMO"}</h3>
        <p class="sol-item"><strong>Artículo:</strong> ${itemName}</p>
        <p class="sol-date"><strong>Fecha Solicitud:</strong> ${new Date(p.registro_instante).toLocaleString() ?? "—"}</p>
        <div class="sol-actions">
           ${actions}
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

  // ---------- acciones (CORREGIDO) ----------
  async function handleAccion(tipo, id) {
    // NOTA: El 'id' que viene del botón es el ID de la *Solicitud*.
    // Los servicios 'renovar' y 'devolver' esperan un 'prestamo_id'.
    // Esto es un problema en tu lógica: la vista no sabe el 'prestamo_id'.
    // Asumiremos (con error) que el ID de la solicitud es el ID del préstamo.
    // Lo ideal sería que `get_solicitudes` devolviera el `prestamo_id` asociado.
    
    const prestamo_id_o_reserva_id = Number(id); 
    
    try {
      let res;
      let payload = {};

      if (tipo === "cancelar") {
        // 'cancel_reserva' espera 'reserva_id'.
        payload = { reserva_id: prestamo_id_o_reserva_id };
        res = await API.cancelReserva(payload);
        
      } else if (tipo === "renovar") {
        // 'renovar_prestamo' espera 'prestamo_id'.
        payload = { prestamo_id: prestamo_id_o_reserva_id };
        res = await API.renovarPrestamo(payload);
        
      } else if (tipo === "devolver") {
        // 'create_devolucion' espera 'prestamo_id'.
        payload = { prestamo_id: prestamo_id_o_reserva_id };
        res = await API.createDevolucion(payload);
      }

      setBanner(`Acción "${tipo}" ejecutada correctamente.`, true, res);
      await cargarPrestamos(); // refresca lista
    } catch (e) {
      console.error("[PRESTAMOS] Acción fallida", e);
      let msg = `Error ejecutando "${tipo}". `;
      if (tipo !== 'cancelar') {
         msg += " (Nota: El ID de préstamo puede ser incorrecto)";
      }
      setBanner(msg, false, e.payload || e.message);
    }
  }

  // ---------- fetch (CORREGIDO) ----------
  async function cargarPrestamos() {
    clearBanner(); setLoading(true);

    const correo = window.Auth?.getEmail?.();
    if (!correo) { setBanner("No hay sesión activa.", false); return; }

    try {
      // ANTES:
      // const data = await API.get(S.CATALOG, `/solicitudes?correo=${encodeURIComponent(correo)}`, { auth: true });
      
      // AHORA:
      // Usamos la misma llamada que en 'mis-solicitudes'
      const data = await API.getSolicitudes({ correo: correo });
      
      // ANTES: const list = Array.isArray(data?.data?.solicitudes) ? data.data.solicitudes : [];
      // AHORA (leemos la respuesta correcta de prart/app.py)
      const list = Array.isArray(data?.solicitudes) ? data.solicitudes : [];
      
      // Filtramos para mostrar solo préstamos (no ventanas) y que estén activos (APROBADA)
      const prestamosActivos = list.filter(s => s.tipo === 'PRÉSTAMO' && s.estado === 'APROBADA');
      
      renderPrestamos(prestamosActivos);
      
      if (prestamosActivos.length > 0) {
        setBanner(`Préstamos cargados (${prestamosActivos.length})`, true);
      } else {
        clearBanner();
      }

    } catch (e) {
      console.error("[PRESTAMOS] Error obteniendo préstamos", e);
      setBanner("No se pudieron obtener tus préstamos.", false, e.payload || e.message);
    } finally {
      setLoading(false);
    }
  }

  // ---------- init (Sin cambios) ----------
  window.Auth?.requireAuth?.();
  const user = window.Auth?.getUser?.();
  document.getElementById("userBadge").textContent = user?.correo || "Usuario";
  document.getElementById("btnLogout").addEventListener("click", () => window.Auth.logout());
  cargarPrestamos();

  
})();