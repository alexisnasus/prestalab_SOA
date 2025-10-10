// catalog.js — Lista + filtros + Solicitar (servicio: prart -> /items, /solicitudes)
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const results = document.getElementById('results');
  const state = document.getElementById('state');
  const form = document.getElementById('filters');
  const q = document.getElementById('q');
  const tipoSelect = document.getElementById('tipo');
  const btnClear = document.getElementById('btnClear');

  const CLP = (n) => {
    const num = Number(n);
    if (Number.isNaN(num)) return '-';
    try { return num.toLocaleString('es-CL', { style: 'currency', currency: 'CLP', maximumFractionDigits: 0 }); }
    catch { return `${num} CLP`; }
  };

  function showState(msg, ok=false) {
    state.textContent = msg;
    state.style.display = 'block';
    state.style.borderColor = ok ? 'rgba(34,197,94,0.35)' : 'rgba(239,68,68,0.35)';
    state.style.color = ok ? '#22c55e' : '#ef4444';
    state.style.background = ok ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)';
  }
  function hideState(){ state.style.display = 'none'; }

  async function ensureUserId() {
    const id = await window.Auth.ensureUserId();
    if (!id) throw new Error('No pudimos obtener tu ID automáticamente. Abre el Dashboard una vez o define tu ID.');
    return id;
  }

  async function crearSolicitudPrestamo() {
    const usuario_id = await ensureUserId();
    const body = { usuario_id, tipo: 'PRÉSTAMO' };
    // POST /prart/solicitudes (vía Bus /route)
    return await API.post(S.CATALOG, '/solicitudes', body, { auth: true });
  }

  function card(item) {
    const {
      id, nombre, tipo, descripcion, cantidad, cantidad_max,
      valor, tarifa_atraso
    } = item;

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

  function wireRequestButtons() {
    results.querySelectorAll('.request-btn').forEach(btn => {
      btn.addEventListener('click', async (ev) => {
        ev.preventDefault();
        const name = ev.currentTarget.closest('.item-card')?.querySelector('.item-title')?.textContent || 'ítem';
        try {
          showState(`Creando solicitud para "${name}"…`, true);
          await crearSolicitudPrestamo();
          showState(`Solicitud creada para "${name}". Queda PENDIENTE de gestión.`, true);
        } catch (e) {
          console.error('[CAT] Solicitar error', e);
          let msg = 'No se pudo crear la solicitud.';
          if (e.message && e.message.includes('ID')) msg = e.message;
          else if (e.payload && (e.payload.detail || e.payload.message || e.payload.error)) {
            msg = e.payload.detail || e.payload.message || e.payload.error;
          }
          showState(msg, false);
        }
      });
    });
  }

  function renderList(items) {
    results.innerHTML = '';
    if (!items || !items.length) {
      results.innerHTML = '<p style="opacity:.8">Sin resultados.</p>';
      return;
    }
    // Poblar combos de tipo (únicos)
    const tipos = Array.from(new Set(items.map(it => it.tipo).filter(Boolean))).sort();
    const current = tipoSelect.value;
    tipoSelect.innerHTML = '<option value="">Todos</option>' + tipos.map(t => `<option value="${t}">${t}</option>`).join('');
    tipoSelect.value = current;

    const frag = document.createDocumentFragment();
    items.forEach(it => frag.appendChild(card(it)));
    results.appendChild(frag);
    wireRequestButtons();
  }

  async function fetchItems({ nombre='', tipo='' } = {}) {
    hideState();
    results.innerHTML = '<p style="opacity:.7">Cargando…</p>';

    const params = new URLSearchParams();
    if (nombre) params.set('nombre', nombre);
    if (tipo) params.set('tipo', tipo);
    const endpoint = '/items' + (params.toString() ? `?${params.toString()}` : '');

    try {
      const data = await API.get(S.CATALOG, endpoint, { auth: true });
      renderList(Array.isArray(data) ? data : []);
      if (!data || !data.length) showState('No se encontraron ítems con ese filtro.', true);
    } catch (e) {
      console.error('[CAT] Error cargando items', e);
      let msg = 'No se pudo cargar el catálogo.';
      if (e.payload && (e.payload.detail || e.payload.message || e.payload.error)) {
        msg = e.payload.detail || e.payload.message || e.payload.error;
      }
      results.innerHTML = '';
      showState(msg, false);
    }
  }

  // Buscar
  form.addEventListener('submit', (ev) => {
    ev.preventDefault();
    const nombre = (q.value || '').trim();
    const tipo = (tipoSelect.value || '').trim();
    fetchItems({ nombre, tipo });
  });

  // Limpiar
  btnClear.addEventListener('click', () => {
    q.value = '';
    tipoSelect.value = '';
    fetchItems({});
  });

  // Primera carga
  fetchItems({});
})();
