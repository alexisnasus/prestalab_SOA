// mis-multas.js — Listar multas del usuario (MULTA) con fallback para obtener usuario_id
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const FINES = S.FINES || 'multa';     // alias del servicio de multas
  const AUTH  = S.AUTH  || 'regist';    // para resolver id por correo si falta

  const wrap  = document.getElementById('multasWrap'); // contenedor de tarjetas/listado
  const state = document.getElementById('state');      // banner de estado
  const btn   = document.getElementById('btnReload');  // botón "Actualizar" 

  // ---------- UI ----------
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

  // ---------- helpers ----------
  async function resolveUserId() {
    // 1) intenta desde localStorage 
    const raw = localStorage.getItem('pl_user_id');
    if (raw && /^\d+$/.test(raw)) return Number(raw);

    // 2) si no está, intenta resolver con REGIST por correo
    const correo = window.Auth?.getEmail?.();
    if (!correo) return null;

    try {
      const r = await API.get(AUTH, `/usuarios?correo=${encodeURIComponent(correo)}`, { auth: true });
      const body = (r && typeof r === 'object' && 'data' in r) ? r.data : r;
      // puede venir como array o como objeto
      const id = Array.isArray(body) ? body[0]?.id : body?.id;
      if (id) {
        try { localStorage.setItem('pl_user_id', String(id)); } catch {}
        return Number(id);
      }
    } catch (_) { /* silencioso */ }

    return null;
  }

  function normalizeMultas(resp) {
    // posibles formatos:
  
    const body = (resp && typeof resp === 'object' && 'data' in resp) ? resp.data : resp;
    if (Array.isArray(body)) return body;
    if (Array.isArray(body?.multas)) return body.multas;
    if (Array.isArray(body?.data)) return body.data;
    return [];
  }

  // ---------- render ----------
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
        <p class="sol-date"><strong>Fecha:</strong> ${m.registro_instante ?? '—'}</p>
      `;
      grid.appendChild(card);
    });

    wrap.appendChild(grid);
  }

  // ---------- flujo principal ----------
  async function cargarMultas() {
    clearBanner();
    loading(true);

    // debe haber sesión
    window.Auth?.requireAuth?.();
    const correo = window.Auth?.getEmail?.();
    if (!correo) {
      loading(false);
      return err('No hay sesión activa.');
    }

    const uid = await resolveUserId();
    if (!uid) {
      loading(false);
      return err('No se pudo obtener tu ID automáticamente. Entra primero a Dashboard o contacta al admin.', { detalle: 'sin_usuario_id' });
    }

    try {
      const resp = await API.get(FINES, `/usuarios/${uid}/multas`, { auth: true });
      const multas = normalizeMultas(resp);
      render(multas);
      ok(`Multas cargadas (${multas.length})`);
    } catch (e) {
      err('No se pudieron obtener tus multas.', { status: e?.status ?? null, raw: e?.payload ?? e });
    } finally {
      loading(false);
    }
  }

  // ---------- init ----------
  document.getElementById('userBadge').textContent =
    window.Auth?.getUser?.()?.correo || 'Usuario';

  document.getElementById('btnLogout')
    ?.addEventListener('click', () => window.Auth.logout());

  btn?.addEventListener('click', cargarMultas);

  cargarMultas();
})();
