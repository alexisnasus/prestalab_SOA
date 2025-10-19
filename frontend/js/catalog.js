// catalog.js — Lista + filtros + Modal para Solicitar o Reservar (servicio: prart)
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const CATALOG_SERVICE = S.CATALOG || 'prart';

  // DOM del catálogo
  const results = document.getElementById('results');
  const state = document.getElementById('state');
  const form = document.getElementById('filters');
  const q = document.getElementById('q');
  const tipoSelect = document.getElementById('tipo');
  const btnClear = document.getElementById('btnClear');

  // DOM del Modal
  const modal = document.getElementById('reserveModal');
  const modalTitle = document.getElementById('modalTitle');
  const modalForm = document.getElementById('modalForm');
  const modalItemId = document.getElementById('modalItemId');
  const dateFields = document.getElementById('dateFields');
  const elInicio = document.getElementById('reserveInicio');
  const elFin = document.getElementById('reserveFin');
  const btnConfirm = document.getElementById('btnConfirmRequest');
  const btnCancel = document.getElementById('btnCancelRequest');
  const modalState = document.getElementById('modalState');

  // ---------- UTILITARIOS UI ----------
  const CLP = (n) => {
    const num = Number(n);
    if (Number.isNaN(num)) return '-';
    try { return num.toLocaleString('es-CL', { style: 'currency', currency: 'CLP', maximumFractionDigits: 0 }); }
    catch { return `${num} CLP`; }
  };

  function showState(msg, ok = false, extra) {
    const el = modal.style.display === 'flex' ? modalState : state;
    el.innerHTML = '';
    const line = document.createElement('div');
    line.textContent = String(msg);
    el.appendChild(line);

    if (extra !== undefined) {
      const pre = document.createElement('pre');
      pre.style.marginTop = '6px';
      pre.style.whiteSpace = 'pre-wrap';
      try { pre.textContent = typeof extra === 'string' ? extra : JSON.stringify(extra, null, 2); }
      catch { pre.textContent = String(extra); }
      el.appendChild(pre);
    }

    el.style.display = 'block';
    el.className = ok ? 'alert alert-ok' : 'alert alert-error'; // Asigna clases para estilo
    el.style.borderColor = ok ? 'rgba(34,197,94,0.35)' : 'rgba(239,68,68,0.35)';
    el.style.color = ok ? '#22c55e' : '#ef4444';
    el.style.background = ok ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)';
  }
  function hideState() { state.style.display = 'none'; modalState.style.display = 'none'; }

  // Lógica para mostrar/ocultar el modal
  const openModal = (itemId, itemName) => {
    modalTitle.textContent = `Solicitar: ${itemName}`;
    modalItemId.value = itemId;
    modal.style.display = 'flex';
  };
  const closeModal = () => {
    modal.style.display = 'none';
    modalForm.reset();
    dateFields.style.display = 'none';
    hideState();
  };

  // ---------- RENDER DE TARJETA ----------
  function card(item) {
    const { id, nombre, tipo, descripcion, cantidad, cantidad_max, valor, tarifa_atraso } = item;
    const el = document.createElement('article');
    el.className = 'card item-card';
    el.innerHTML = `
      <h3 class="item-title">${nombre || '—'}</h3>
      <p class="item-desc">${descripcion || ''}</p>
      <div class="item-meta">
        <span class="pill">${tipo || '—'}</span>
        <span class="pill">Stock (tabla item): ${cantidad ?? '—'}</span>
        <span class="pill">Máx/usuario: ${cantidad_max ?? '—'}</span>
      </div>
      <div class="item-prices">
        <div><small>Valor ref.</small><div class="price">${CLP(valor)}</div></div>
        <div><small>Tarifa atraso</small><div class="price">${CLP(tarifa_atraso)}</div></div>
      </div>
      <div class="actions">
        <button class="btn request-btn" data-id="${id}">Solicitar</button>
      </div>
    `;
    return el;
  }

  // ---------- EVENTOS ----------
  // Evento para abrir el modal al hacer clic en "Solicitar"
  results.addEventListener('click', (ev) => {
    const requestBtn = ev.target.closest('.request-btn');
    if (requestBtn) {
      const card = requestBtn.closest('.item-card');
      const itemId = requestBtn.dataset.id;
      const itemName = card.querySelector('.item-title').textContent;
      openModal(itemId, itemName);
    }
  });

  // Eventos dentro del modal
  modalForm.addEventListener('change', (e) => {
    if (e.target.name === 'requestType') {
      dateFields.style.display = e.target.value === 'VENTANA' ? 'grid' : 'none';
    }
  });

  btnCancel.addEventListener('click', closeModal);

  // Lógica principal al confirmar en el modal
  modalForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideState();

    const requestType = modalForm.querySelector('input[name="requestType"]:checked').value;
    const itemId = modalItemId.value;
    const correo = window.Auth?.getEmail?.();

    if (!correo) {
      showState('No se pudo identificar tu correo. Inicia sesión de nuevo.', false);
      return;
    }

    btnConfirm.disabled = true;
    btnConfirm.textContent = 'Procesando...';

    try {
      if (requestType === 'PRESTAMO') {
        // --- Lógica de Solicitud de Préstamo Simple ---
        const payload = { tipo: 'PRÉSTAMO', correo, usuario_id: window.Auth?.getUserId?.() };
        const res = await API.post(CATALOG_SERVICE, '/solicitudes', payload, { auth: true });
        showState('Solicitud de préstamo creada. Queda pendiente de aprobación.', true);
        
      } else if (requestType === 'VENTANA') {
        // --- Lógica de Reserva con Ventana de Tiempo ---
        const inicio = elInicio.value;
        const fin = elFin.value;

        if (!inicio || !fin) throw new Error('Debes seleccionar las fechas de inicio y fin.');
        if (new Date(fin) <= new Date(inicio)) throw new Error('La fecha de fin debe ser posterior a la de inicio.');

        // 1. Crear solicitud de tipo 'VENTANA'
        const solPayload = { tipo: 'VENTANA', correo, usuario_id: window.Auth?.getUserId?.() };
        const solRes = await API.post(CATALOG_SERVICE, '/solicitudes', solPayload, { auth: true });
        const solicitudId = solRes?.solicitud_id || solRes?.id;
        if (!solicitudId) throw new Error('Fallo al crear la solicitud previa a la reserva.');

        // 2. Crear la reserva
        const reservaPayload = {
          solicitud_id: solicitudId,
          item_existencia_id: parseInt(itemId, 10), // El backend debería resolver la existencia disponible
          inicio: new Date(inicio).toISOString(),
          fin: new Date(fin).toISOString()
        };
        await API.post(CATALOG_SERVICE, '/reservas', reservaPayload, { auth: true });
        showState('¡Reserva creada exitosamente!', true);
      }
      setTimeout(closeModal, 1500); // Cierra el modal después de un breve éxito
    } catch (err) {
      const errorMsg = err?.payload?.detail || err.message || 'Ocurrió un error.';
      showState(errorMsg, false);
    } finally {
      btnConfirm.disabled = false;
      btnConfirm.textContent = 'Confirmar';
    }
  });

  // ---------- RENDER LISTADO Y FETCH (lógica existente) ----------
  function renderList(items) {
    results.innerHTML = '';
    if (!items || !items.length) {
      results.innerHTML = '<p style="opacity:.8">Sin resultados.</p>';
      return;
    }
    const tipos = Array.from(new Set(items.map(it => it.tipo).filter(Boolean))).sort();
    const current = tipoSelect.value;
    tipoSelect.innerHTML = '<option value="">Todos</option>' + tipos.map(t => `<option value="${t}">${t}</option>`).join('');
    tipoSelect.value = current;
    const frag = document.createDocumentFragment();
    items.forEach(it => frag.appendChild(card(it)));
    results.appendChild(frag);
  }

  async function fetchItems({ nombre = '', tipo = '' } = {}) {
    hideState();
    results.innerHTML = '<p style="opacity:.7">Cargando…</p>';
    const params = new URLSearchParams();
    if (nombre) params.set('nombre', nombre);
    if (tipo) params.set('tipo', tipo);
    const endpoint = '/items' + (params.toString() ? `?${params}` : '');
    try {
      const data = await API.get(CATALOG_SERVICE, endpoint, { auth: true });
      renderList(Array.isArray(data) ? data : []);
      if (!data || !data.length) showState('No se encontraron ítems con ese filtro.', true);
    } catch (e) {
      console.error('[CAT] Error cargando items', e);
      let msg = 'No se pudo cargar el catálogo.';
      if (e?.payload?.detail) msg = e.payload.detail;
      results.innerHTML = '';
      showState(msg, false, e?.payload ?? null);
    }
  }

  // ---------- EVENTOS DE FILTROS (lógica existente) ----------
  form.addEventListener('submit', (ev) => {
    ev.preventDefault();
    const nombre = (q.value || '').trim();
    const tipo = (tipoSelect.value || '').trim();
    fetchItems({ nombre, tipo });
  });

  btnClear.addEventListener('click', () => {
    q.value = '';
    tipoSelect.value = '';
    fetchItems({});
  });

  // ---------- CARGA INICIAL ----------
  hideState();
  fetchItems({});
})();