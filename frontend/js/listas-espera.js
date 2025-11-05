// listas-espera.js — (CORREGIDO PARA NUEVA API)
(function () {
  const S        = window.PRESTALAB?.SERVICES || {};
  const LIST     = S.WAITLIST || S.lista;   // servicio lista de espera
  const CATALOG  = S.CATALOG  || S.prart;   // servicio items/solicitudes

  // DOM
  const elState   = document.getElementById("waitState");
  const elList    = document.getElementById("catalogList");
  const elSearch  = document.getElementById("waitSearch");
  const btnRef    = document.getElementById("btnWaitRefresh");
  const btnAll    = document.getElementById("btnVerTodo"); // opcional

  // Estado local
  let ALL_ITEMS = [];
  let PAGE_SIZE = 24;
  let page = 1;

  // -------- storage: recordamos solicitud_id por item (Sin cambios) ----------
  const userEmail = () => (window.Auth?.getEmail?.() || "").toLowerCase();
  const userId    = () => window.Auth?.getUserId?.() || localStorage.getItem('pl_user_id') || null;
  const LS_KEY    = () => `pl_wait_solicitudes:${userEmail()}`;

  function getWaitMap() {
    try { return JSON.parse(localStorage.getItem(LS_KEY()) || "{}"); }
    catch { return {}; }
  }
  function setWaitMap(map) { localStorage.setItem(LS_KEY(), JSON.stringify(map || {})); }
  function rememberJoin(item_id, solicitud_id) {
    const map = getWaitMap(); map[item_id] = solicitud_id; setWaitMap(map);
  }
  function forgetJoin(item_id) {
    const map = getWaitMap(); delete map[item_id]; setWaitMap(map);
  }

  // ---------- Helpers UI (Sin cambios) ----------
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

  // ---------- Normalizador (Sin cambios) ----------
  function normalizeCatalog(resp) {
    // prart/app.py devuelve { "items": [...] }
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

  // ---------- API: traerse TODO el catálogo (CORREGIDO) ----------
  async function fetchAllCatalog() {
    try {
      // ANTES: Múltiples llamadas con API.get y paths manuales
      // AHORA:
      const res = await API.getAllItems(); // Llama a la nueva función
      
      let list = normalizeCatalog(res);
      if (list.length) return uniqueBy(list, x => x.id);
      
    } catch (e) {
      console.error("Error al cargar el catálogo:", e);
    }
    return []; // Devuelve vacío si falla
  }

  function uniqueBy(arr, key) {
    const seen = new Set(); const out = [];
    for (const x of arr) { const k = key(x); if (!seen.has(k)) { seen.add(k); out.push(x); } }
    return out;
  }

  // ---------- Crear solicitud + unirse (CORREGIDO) ----------
  async function crearSolicitud(tipo = 'VENTANA') {
    const correo = userEmail();
    if (!correo) throw new Error('No hay sesión activa.');
    const uid = userId();
    const body = { tipo, correo };
    if (uid && /^\d+$/.test(String(uid))) body.usuario_id = Number(uid);

    // ANTES: const res = await API.post(CATALOG, '/solicitudes', body, { auth: true });
    // AHORA:
    const res = await API.createSolicitud(body);
    
    // El servicio prart/app.py devuelve { "solicitud_id": ... }
    const solicitud_id = res?.solicitud_id ?? res?.id ?? res?.data?.solicitud_id;
    if (!solicitud_id) throw new Error('No se obtuvo solicitud_id al crear la solicitud.');
    return solicitud_id;
  }

  // ---------- Detección de presencia en cola (CORREGIDO) ----------
  function arrayFirst(arrLike) {
    if (Array.isArray(arrLike)) return arrLike;
    if (arrLike && typeof arrLike === 'object') {
      // El servicio lista/app.py devuelve { "registros": [...] }
      for (const k of ['registros','lista','data','items']) {
        if (Array.isArray(arrLike[k])) return arrLike[k];
      }
    }
    return [];
  }

  function extractUserFields(r) { // (Sin cambios)
    const lower = (s) => (s || '').toString().toLowerCase();
    return {
      regId: r?.id ?? r?.registro_id ?? r?.lista_id ?? null,
      solicitudId: r?.solicitud_id ?? r?.solicitud?.id ?? r?.solicitudId ?? null,
      usuarioId: r?.usuario_id ?? r?.usuario?.id ?? r?.solicitud?.usuario_id ?? null,
      correo: lower(r?.correo || r?.email || r?.usuario?.correo || r?.solicitud?.correo || r?.solicitud?.email)
    };
  }

  function isMe(rFields, rememberedSolicitudId) { // (Sin cambios)
    const myEmail = userEmail();
    const myUid   = userId();
    if (rememberedSolicitudId && String(rFields.solicitudId) === String(rememberedSolicitudId)) return true;
    if (myUid && rFields.usuarioId && String(rFields.usuarioId) === String(myUid)) return true;
    if (myEmail && rFields.correo && rFields.correo === myEmail) return true;
    return false;
  }

  async function getQueueInfo(item_id) {
    const map = getWaitMap();
    const remembered = map[String(item_id)] || null;

    try {
      // ANTES: const det = await API.get(LIST, `/lista-espera/${item_id}`, { auth: true });
      // AHORA:
      const payload = { item_id: Number(item_id) };
      const det = await API.getListaEspera(payload); // Llama a la nueva API
      
      const registros = arrayFirst(det); // Esto buscará det.registros
      const count = registros.length;

      let myPos = null, myRegId = null, mySolicitudId = null;
      for (let i = 0; i < registros.length; i++) {
        const rf = extractUserFields(registros[i]);
        if (isMe(rf, remembered)) {
          myPos = i + 1;
          myRegId = rf.regId || null;
          mySolicitudId = rf.solicitudId || remembered || null;
          break;
        }
      }

      // (Lógica de sync sin cambios)
      if (!remembered && mySolicitudId) rememberJoin(String(item_id), String(mySolicitudId));
      if (remembered && myPos === null) forgetJoin(String(item_id));

      return { count, myPos, myRegId };
    } catch (e) {
      // Si la API falla (ej. 404 porque no hay lista), devuelve nulo
      // El servicio 'lista' devuelve error si no hay registros
      return { count: 0, myPos: null, myRegId: null };
    }
  }

  // ---------- Unirse / Salir (CORREGIDO) ----------
  async function unirmeALista(item_id, cardEl) {
    clearMsg();
    if (!item_id || !/^\d+$/.test(String(item_id))) { show("Ítem inválido (falta id).", false); return; }

    // PRE-CHEQUEO (Sin cambios)
    const pre = await getQueueInfo(item_id);
    if (pre.myRegId) {
      await enrichCardQueue(cardEl, item_id);
      show(pre.myPos ? `Ya estás en esta lista (posición #${pre.myPos}).` : `Ya estás en esta lista.`, true);
      return;
    }

    try {
      cardEl?.querySelector('button[data-join]')?.setAttribute('disabled', 'disabled');
      // 1. Crear solicitud (ya está corregida)
      const solicitud_id = await crearSolicitud('VENTANA'); 

      // 2. Unirse a la lista
      const payload = {
        solicitud_id: solicitud_id,
        item_id: Number(item_id),
        estado: 'EN ESPERA'
      };
      
      // ANTES: await API.post(LIST, '/lista-espera', payload, { auth: true });
      // AHORA:
      await API.createListaEspera(payload); // Llama a la nueva API
      
      rememberJoin(String(item_id), String(solicitud_id));

      // refrescar contador/estado de la card
      await enrichCardQueue(cardEl, item_id);
      show(`Listo: te sumaste a la lista.`, true);
    } catch (e) {
      let msg = e?.payload?.detail || e?.payload?.message || e?.payload?.error || e?.message || 'No se pudo sumar a la lista.';
      show(msg, false);
    } finally {
      cardEl?.querySelector('button[data-join]')?.removeAttribute('disabled');
    }
  }

  async function salirDeLista(registro_id, item_id, cardEl) {
    clearMsg();
    try {
      cardEl?.querySelector('[data-leave]')?.setAttribute('disabled', 'disabled');
      
      // ANTES: await API.delete(LIST, `/lista-espera/${registro_id}`, { auth: true });
      // AHORA:
      // El servicio 'lista' usa 'update' con estado 'CANCELADA'
      const payload = {
        id: Number(registro_id),
        estado: 'CANCELADA'
      };
      await API.updateListaEspera(payload); // Llama a la nueva API

      forgetJoin(String(item_id));
      await enrichCardQueue(cardEl, item_id);
      show('Saliste de la lista de espera.', true);
    } catch (e) {
      let msg = e?.payload?.detail || e?.payload?.message || e?.payload?.error || e?.message || 'No se pudo salir de la lista.';
      show(msg, false);
    } finally {
      cardEl?.querySelector('[data-leave]')?.removeAttribute('disabled');
    }
  }

  // ---------- Render (Sin cambios) ----------
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

    const end   = PAGE_SIZE * page;
    const view  = filtered.slice(0, end);

    elList.innerHTML = "";
    if (!view.length) {
      elList.innerHTML = '<p style="opacity:.8">No hay equipos para mostrar.</p>';
      return;
    }

    const frag = document.createDocumentFragment();
    view.forEach(it => {
      const card = document.createElement('article');
      card.className = 'sol-card';
      card.setAttribute('data-item', it.id);
      const meta = [it.marca, it.modelo].filter(Boolean).join(" · ");
      const badge = it.categoria ? `<span class="sol-badge">${escapeHtml(it.categoria)}</span>` : '';

      card.innerHTML = `
        <div class="sol-top">
          <span class="sol-id">Item:${it.id}</span>
          ${badge}
        </div>
        <h3 class="sol-title">${escapeHtml(it.nombre)}</h3>
        <p class="sol-item"><strong>Marca/Modelo:</strong> ${escapeHtml(meta || '—')}</p>

        <div class="queue-line" style="display:flex;align-items:center;gap:.5rem;margin:.35rem 0 .5rem 0">
          <span class="queue-pill" data-qcount style="font-size:.85rem;opacity:.85;">En cola: —</span>
          <span class="queue-you" data-qyou style="font-size:.85rem;color:#a5b4fc;"></span>
        </div>

        <div class="sol-actions" style="display:flex;gap:.5rem;justify-content:flex-end;">
          <button class="btn btn-small" data-join="${it.id}">Unirme a la lista</button>
          <button class="btn btn-small btn-danger" data-leave style="display:none">Salir de la lista</button>
        </div>
      `;
      frag.appendChild(card);
    });
    elList.appendChild(frag);

    // “Cargar más”
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

    const showing = Math.min(end, filtered.length);
    show(`Mostrando ${showing} de ${filtered.length} equipos · Catálogo total: ${ALL_ITEMS.length}`, true);

    hydrateVisibleQueues();
  }

  // Concurrencia limitada (Sin cambios)
  async function hydrateVisibleQueues(concurrency = 6) {
    const cards = Array.from(elList.querySelectorAll('.sol-card'));
    let i = 0;
    async function worker() {
      while (i < cards.length) {
        const card = cards[i++];
        const itemId = card.getAttribute('data-item');
        await enrichCardQueue(card, itemId);
      }
    }
    const workers = Array.from({ length: Math.min(concurrency, cards.length) }, worker);
    await Promise.all(workers);
  }

  // enrichCardQueue (Sin cambios)
  async function enrichCardQueue(cardEl, item_id) {
    const qCountEl = cardEl.querySelector('[data-qcount]');
    const qYouEl   = cardEl.querySelector('[data-qyou]');
    const joinBtn  = cardEl.querySelector('[data-join]');
    const leaveBtn = cardEl.querySelector('[data-leave]');

    const { count, myPos, myRegId } = await getQueueInfo(item_id);

    qCountEl.textContent = `En cola: ${count === null ? '—' : count}`;

    if (myRegId) {
      qYouEl.textContent = myPos ? `· Tu posición: #${myPos}` : '· Ya estás en la lista';
      leaveBtn.style.display = 'inline-block';
      leaveBtn.setAttribute('data-leave', myRegId);
      leaveBtn.setAttribute('data-item', item_id);
      joinBtn.style.display = 'none';
    } else {
      qYouEl.textContent = '';
      leaveBtn.style.display = 'none';
      leaveBtn.removeAttribute('data-leave');
      leaveBtn.removeAttribute('data-item');
      joinBtn.style.display = 'inline-block';
    }
  }

  // ---------- Flujo inicial (CORREGIDO) ----------
  async function boot() {
    window.Auth?.requireAuth?.();
    clearMsg();
    setLoading(true);
    try {
      ALL_ITEMS = await fetchAllCatalog(); // Esta función ya está corregida
      page = 1;
      render();
    } catch (e) {
      show('No se pudo cargar el catálogo.', false);
    } finally {
      setLoading(false);
    }
  }

  // ---------- Eventos (Sin cambios) ----------
  elSearch.addEventListener('input', () => { page = 1; render(); });
  btnRef?.addEventListener('click', (e) => { e.preventDefault(); boot(); });
  btnAll?.addEventListener('click', (e) => { e.preventDefault(); elSearch.value=""; page=1; render(); });

  // delegación: unirse / salir (Sin cambios)
  elList.addEventListener('click', async (ev) => {
    const join = ev.target.closest('[data-join]');
    if (join) {
      ev.preventDefault();
      const item_id = join.getAttribute('data-join');
      const card = join.closest('.sol-card');
      if (confirm('¿Quieres unirte a la lista de espera de este ítem?')) {
        await unirmeALista(item_id, card); // Esta función ya está corregida
      }
      return;
    }
    const leave = ev.target.closest('[data-leave]');
    if (leave && leave.getAttribute('data-leave')) {
      ev.preventDefault();
      const regId  = leave.getAttribute('data-leave');
      const itemId = leave.getAttribute('data-item');
      const card = leave.closest('.sol-card');
      if (confirm('¿Seguro que quieres salir de la lista?')) {
        await salirDeLista(regId, itemId, card); // Esta función ya está corregida
      }
    }
  });

  // go!
  boot();

  
  // ---------- init (LIMPIO Y CORRECTO) ----------
  // Este bloque estaba duplicado y con errores.
  // Lo limpiamos para que solo haga lo necesario.
  (function init() {
    window.Auth?.requireAuth?.();
    const user = window.Auth?.getUser?.();
    document.getElementById("userBadge").textContent = user?.correo || "Usuario";
    document.getElementById("btnLogout").addEventListener("click", () => window.Auth.logout());
  })();

  // --- FIN DEL CÓDIGO BASURA QUE ESTABA AQUÍ ---
  
})();