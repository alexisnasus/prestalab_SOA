// mis-multas.js — (CORREGIDO PARA NUEVA API)
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const FINES = S.FINES || 'multa';     // alias del servicio de multas
  
  const wrap  = document.getElementById('multasWrap'); // contenedor de tarjetas/listado
  const state = document.getElementById('state');      // banner de estado
  const btn   = document.getElementById('btnReload');  // botón "Actualizar" 

  // ---------- UI (Sin cambios) ----------
  function banner(msg, ok=false, extra=null) {
    state.innerHTML = '';
    const p = document.createElement('div');
    p.textContent = String(msg);
    state.appendChild(p);

    if (extra) {
      const pre = document.createElement('pre');
      pre.style.whiteSpace = 'pre-wrap';
      pre.style.marginTop  = '6px';
      try { pre.textContent = typeof extra === 'string' ? extra : JSON.stringify(extra, null, 2); }
      catch { pre.textContent = String(extra); }
      state.appendChild(pre);
    }

    state.style.display     = 'block';
    state.style.borderColor = ok ? 'rgba(34,197,94,0.35)' : 'rgba(239,68,68,0.35)';
    state.style.color       = ok ? '#22c55e'              : '#ef4444';
    state.style.background  = ok ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)';
  }
  function ok(msg)  { banner(msg, true); }
  function err(msg, extra) { banner(msg, false, extra); }
  function clearBanner(){ state.style.display = 'none'; }
  function loading(on=true){ wrap.innerHTML = on ? '<p style="opacity:.7">Cargando…</p>' : ''; }

  // ---------- helpers (CORREGIDO) ----------
  
  // --- ELIMINADA LA FUNCIÓN `resolveUserId` ---
  // Ya no es necesaria. `window.Auth.getUserId()` es suficiente.

  function normalizeMultas(resp) {
    // El servicio multa/app.py devuelve { "multas": [...] }
    //
    const body = (resp && typeof resp === 'object') ? resp : {};
    
    if (Array.isArray(body?.multas)) return body.multas;
    if (Array.isArray(body?.data)) return body.data; // Fallback
    if (Array.isArray(body)) return body; // Fallback
    return [];
  }

  // ---------- render (Sin cambios) ----------
  function render(list) {
    wrap.innerHTML = '';
    const items = Array.isArray(list) ? list : [];

    if (!items.length) {
      wrap.innerHTML = '<p style="opacity:.8">No tienes multas registradas.</p>';
      return;
    }

    const grid = document.createElement('div');
    grid.className = 'sol-grid'; // estilos de tarjetas

    items.forEach((m) => {
      const card = document.createElement('article');
      card.className = 'sol-card';
      card.innerHTML = `
        <div class="sol-top">
          <span class="sol-id">#${m.id ?? '—'}</span>
          <span class="sol-badge ${String(m.estado || '').toLowerCase()}">${m.estado ?? '—'}</span>
        </div>
        <h3 class="sol-title">Multa</h3>
        <p class="sol-item"><strong>Motivo:</strong> ${m.motivo ?? '—'}</p>
        <p class="sol-item"><strong>Monto:</strong> ${m.valor != null ? `$${m.valor}` : '—'}</p>
        <p class="sol-date"><strong>Fecha:</strong> ${new Date(m.registro_instante).toLocaleString() ?? '—'}</p>
      `;
      grid.appendChild(card);
    });

    wrap.appendChild(grid);
  }

  // ---------- flujo principal (CORREGIDO) ----------
  async function cargarMultas() {
    clearBanner();
    loading(true);

    // debe haber sesión
    window.Auth?.requireAuth?.();
    
    // Obtenemos el ID de usuario directamente de auth.js
    const uid = window.Auth?.getUserId?.();
    
    if (!uid) {
      loading(false);
      // Si no hay ID, es porque el login (auth.js) falló en guardarlo.
      return err('No se pudo obtener tu ID de usuario. Por favor, inicia sesión de nuevo.', { detalle: 'sin_usuario_id' });
    }

    try {
      // --- ESTE ES EL CAMBIO ---
      // ANTES:
      // const resp = await API.get(FINES, `/usuarios/${uid}/multas`, { auth: true });
      
      // AHORA:
      const payload = { usuario_id: uid };
      const resp = await API.getMultasUsuario(payload); // Llama a la nueva API
      // --- FIN DEL CAMBIO ---

      const multas = normalizeMultas(resp);
      render(multas);
      
      if (multas.length > 0) {
        ok(`Multas cargadas (${multas.length})`);
      } else {
        clearBanner(); // No mostrar banner si solo dice "0 cargadas"
      }
      
    } catch (e) {
      err('No se pudieron obtener tus multas.', { status: e?.status ?? null, raw: e?.payload ?? e.message });
    } finally {
      loading(false);
    }
  }

  // ---------- init (Sin cambios) ----------
  document.getElementById('userBadge').textContent =
    window.Auth?.getUser?.()?.correo || 'Usuario';

  document.getElementById('btnLogout')
    ?.addEventListener('click', () => window.Auth.logout());

  btn?.addEventListener('click', cargarMultas);

  cargarMultas();
})();