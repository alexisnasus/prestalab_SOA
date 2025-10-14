// listas-espera.js — Catálogo completo + filtro local + "Unirme a la lista"
(function () {
  const S        = window.PRESTALAB?.SERVICES || {};
  const LIST     = S.WAITLIST || S.lista;   // servicio lista de espera
  const CATALOG  = S.CATALOG  || S.prart;   // servicio items/solicitudes

  // DOM
  const elState   = document.getElementById("waitState");
  const elList    = document.getElementById("catalogList");
  const elSearch  = document.getElementById("waitSearch");
  const btnRef    = document.getElementById("btnWaitRefresh");
  const btnAll    = document.getElementById("btnVerTodo"); // opcional si lo tienes

  // Estado local
  let ALL_ITEMS = [];
  let PAGE_SIZE = 24;
  let page = 1;

  // ---------- Helpers UI ----------
  const show = (msg, ok=false) => {
    elState.textContent = msg;
    elState.style.display     = "block";
    elState.style.border      = "1px solid " + (ok ? "rgba(34,197,94,.35)" : "rgba(239,68,68,.35)");
    elState.style.color       = ok ? "#22c55e" : "#ef4444";
    elState.style.background  = ok ? "rgba(34,197,94,.08)" : "rgba(239,68,68,.08)";
    elState.style.padding     = ".5rem .75rem";
    elState.style.borderRadius= ".5rem";
    elState.style.margin      = ".5rem 0";
  };
  const clearMsg = () => (elState.style.display = "none");
  const setLoading = (on=true) => {
    elList.innerHTML = on ? '<p style="opacity:.7">Cargando catálogo…</p>' : '';
    [btnRef, btnAll, elSearch].forEach(x => x && (x.disabled = on));
  };
  const escapeHtml = (s) =>
    String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
             .replace(/"/g,'&quot;').replace(/'/g,'&#39;');

  // ---------- Normalizador ----------
  function normalizeCatalog(resp) {
    const arr = Array.isArray(resp) ? resp
             : Array.isArray(resp?.items) ? resp.items
             : Array.isArray(resp?.data) ? resp.data
             : [];
    return arr.map(it => ({
      id: it?.id ?? it?.item_id,
      nombre: it?.nombre ?? it?.item_nombre ?? 'Ítem',
      tipo: it?.tipo ?? '',
      marca: it?.marca ?? '',
      modelo: it?.modelo ?? '',
      categoria: it?.categoria ?? ''
    })).filter(x => x.id);
  }

  // ---------- API: traerse TODO el catálogo (best-effort) ----------
  async function fetchAllCatalog() {
    // 1) intento: gran límite
    const tryPaths = [
      '/items?limit=1000',
      '/items?limit=500',
      '/items'
    ];
    for (const path of tryPaths) {
      try {
        const res  = await API.get(CATALOG, path, { auth: true });
        let list   = normalizeCatalog(res);

        // 2) si el backend expone paginación, intenta seguirla
        let next = res?.next || res?.next_page || res?.links?.next;
        let offset = res?.next_offset || null;
        let guard = 0;
        while ((next || offset) && guard < 10) {
          guard++;
          try {
            const more = next
              ? await API.get(CATALOG, next, { auth: true })
              : await API.get(CATALOG, `/items?offset=${offset}`, { auth: true });
            list = list.concat(normalizeCatalog(more));
            next = more?.next || more?.next_page || more?.links?.next;
            offset = more?.next_offset || null;
          } catch { break; }
        }

        if (list.length) return uniqueBy(list, x => x.id);
      } catch (_) { /* probar el siguiente */ }
    }
    return [];
  }

  function uniqueBy(arr, key) {
    const seen = new Set(); const out = [];
    for (const x of arr) { const k = key(x); if (!seen.has(k)) { seen.add(k); out.push(x); } }
    return out;
  }

  // ---------- Crear solicitud + unirse a lista ----------
  async function crearSolicitud(tipo = 'VENTANA') {
    const correo = window.Auth?.getEmail?.();
    if (!correo) throw new Error('No hay sesión activa.');
    const legacyId = window.Auth?.getUserId?.() || localStorage.getItem('pl_user_id');
    const body = { tipo, correo };
    if (legacyId && /^\d+$/.test(String(legacyId))) body.usuario_id = Number(legacyId);

    const res = await API.post(CATALOG, '/solicitudes', body, { auth: true });
    const solicitud_id = res?.solicitud_id ?? res?.id ?? res?.data?.solicitud_id;
    if (!solicitud_id) throw new Error('No se obtuvo solicitud_id al crear la solicitud.');
    return solicitud_id;
  }

  async function unirmeALista(item_id, cardEl) {
    clearMsg();
    if (!item_id || !/^\d+$/.test(String(item_id))) {
      show("Ítem inválido (falta id).", false);
      return;
    }
    try {
      cardEl?.querySelector('button[data-join]')?.setAttribute('disabled', 'disabled');
      const solicitud_id = await crearSolicitud('VENTANA');

      await API.post(LIST, '/lista-espera', {
        solicitud_id,
        item_id: Number(item_id),
        estado: 'EN ESPERA'
      }, { auth: true });

      // posición (best-effort)
      let pos = null;
      try {
        const det = await API.get(LIST, `/lista-espera/${item_id}`, { auth: true });
        const registros = det?.registros || [];
        const idx = registros.findIndex(r => Number(r.solicitud_id) === Number(solicitud_id));
        if (idx >= 0) pos = idx + 1;
      } catch {}

      show(pos ? `Listo: te sumaste (posición #${pos}).` : `Listo: te sumaste a la lista.`, true);
    } catch (e) {
      let msg = 'No se pudo sumar a la lista.';
      if (e?.payload?.detail || e?.payload?.message || e?.payload?.error) {
        msg = e.payload.detail || e.payload.message || e.payload.error;
      } else if (e?.message) msg = e.message;
      show(msg, false);
    } finally {
      cardEl?.querySelector('button[data-join]')?.removeAttribute('disabled');
    }
  }

  // ---------- Render ----------
  function render() {
    const term = (elSearch.value || '').trim().toLowerCase();
    const filtered = term
      ? ALL_ITEMS.filter(x => (
          (x.nombre||'').toLowerCase().includes(term) ||
          (x.marca||'').toLowerCase().includes(term)  ||
          (x.modelo||'').toLowerCase().includes(term) ||
          (x.categoria||'').toLowerCase().includes(term)
        ))
      : ALL_ITEMS.slice();

    // paginado front
    const start = 0;
    const end   = PAGE_SIZE * page;
    const view  = filtered.slice(start, end);

    elList.innerHTML = "";
    if (!view.length) {
      elList.innerHTML = '<p style="opacity:.8">No hay equipos para mostrar.</p>';
      return;
    }

    const frag = document.createDocumentFragment();
    view.forEach(it => {
      const card = document.createElement('article');
      card.className = 'sol-card';
      const meta = [it.marca, it.modelo].filter(Boolean).join(" · ");
      const badge = it.categoria ? `<span class="sol-badge">${escapeHtml(it.categoria)}</span>` : '';

      card.innerHTML = `
        <div class="sol-top">
          <span class="sol-id">Item:${it.id}</span>
          ${badge}
        </div>
        <h3 class="sol-title">${escapeHtml(it.nombre)}</h3>
        <p class="sol-item"><strong>Marca/Modelo:</strong> ${escapeHtml(meta || '—')}</p>
        <div class="sol-actions">
          <button class="btn btn-small" data-join="${it.id}">Unirme a la lista</button>
        </div>
      `;
      frag.appendChild(card);
    });

    elList.appendChild(frag);

    // botón "Cargar más"
    const moreNeeded = end < filtered.length;
    let moreBtn = document.getElementById('btnLoadMore');
    if (moreNeeded) {
      if (!moreBtn) {
        moreBtn = document.createElement('button');
        moreBtn.id = 'btnLoadMore';
        moreBtn.className = 'btn btn-ghost';
        moreBtn.style.marginTop = '12px';
        moreBtn.textContent = 'Cargar más';
        moreBtn.addEventListener('click', () => { page++; render(); });
        elList.parentElement.appendChild(moreBtn);
      }
      moreBtn.style.display = 'inline-block';
    } else if (moreBtn) {
      moreBtn.style.display = 'none';
    }

    // estado
    const showing = Math.min(end, filtered.length);
    show(`Mostrando ${showing} de ${filtered.length} equipos · Catálogo total: ${ALL_ITEMS.length}`, true);
  }

  // ---------- Flujo inicial ----------
  async function boot() {
    window.Auth?.requireAuth?.();
    clearMsg();
    setLoading(true);
    try {
      ALL_ITEMS = await fetchAllCatalog();
      page = 1;
      render();
    } catch (e) {
      show('No se pudo cargar el catálogo.', false);
    } finally {
      setLoading(false);
    }
  }

  // ---------- Eventos ----------
  elSearch.addEventListener('input', () => { page = 1; render(); });
  btnRef?.addEventListener('click', (e) => { e.preventDefault(); boot(); });
  btnAll?.addEventListener('click', (e) => { e.preventDefault(); elSearch.value=""; page=1; render(); });

  // delegación: botón "Unirme a la lista"
  elList.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-join]');
    if (!btn) return;
    ev.preventDefault();
    const item_id = btn.getAttribute('data-join');
    const card = btn.closest('.sol-card');
    if (confirm('¿Quieres unirte a la lista de espera de este ítem?')) {
      unirmeALista(item_id, card);
    }
  });

  // go!
  boot();
})();
