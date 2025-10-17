// sugerencias.js — VERSIÓN FINAL CORREGIDA
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const SUG = S.SUGGESTIONS || S.SUGGEST || "sugit";

  // DOM
  const elState = document.getElementById('sugState');
  const panelEnviar = document.getElementById('panel-enviar');
  const panelAdmin = document.getElementById('panel-admin');
  const tabAdminBtn = document.getElementById('tabAdmin');
  const btnBackToUser = document.getElementById('btnBackToUser');

  // Form
  const form = document.getElementById('sugForm');
  const inTitulo = document.getElementById('sugTitulo');
  const inDetalle = document.getElementById('sugDetalle');
  const count = document.getElementById('sugCount');

  // Mis sugerencias
  const mySearch = document.getElementById('mySearch');
  const myStatus = document.getElementById('myStatus');
  const btnMyRef = document.getElementById('btnMyRefresh');
  const myTable = document.getElementById('myTable');

  // Admin
  const admSearch = document.getElementById('admSearch');
  const admStatus = document.getElementById('admStatus');
  const btnAdmRef = document.getElementById('btnAdmRefresh');
  const admTable = document.getElementById('admTable');

  let ALL = [];
  let MINE = [];
  const MAX_LEN = 800;
  
  // ===== CORRECCIÓN: Definimos la función updateCount al principio =====
  function updateCount() {
    if (!count || !inDetalle) return; // Chequeo de seguridad
    const n = (inDetalle.value || '').length;
    count.textContent = `${n}/${MAX_LEN}`;
    if (n > MAX_LEN) {
        inDetalle.value = inDetalle.value.substring(0, MAX_LEN);
    }
  }

  // ==== Helpers ====
  const show = (msg, ok = false) => {
    elState.textContent = msg;
    elState.style.display = "block";
    elState.style.borderColor = ok ? 'rgba(34,197,94,0.35)' : 'rgba(239,68,68,0.35)';
    elState.style.color = ok ? '#22c55e' : '#ef4444';
    elState.style.background = ok ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)';
  };
  const clearMsg = () => (elState.style.display = "none");
  const escapeHtml = (s) => String(s).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'})[m]);
  const badge = (e) => {
    const s = (e||'').toUpperCase();
    if (s === 'APROBADA') return `<span class="badge b-ok">Aprobada</span>`;
    if (s === 'RECHAZADA') return `<span class="badge b-no">Rechazada</span>`;
    return `<span class="badge b-pend">Pendiente</span>`;
  };

  function getMyId() {
    let uid = window.Auth?.getUserId?.();
    if (uid) return uid;
    const user = window.Auth?.getUser?.();
    if (user?.id) {
        localStorage.setItem('pl_user_id', String(user.id));
        return user.id;
    }
    return null;
  }
  
  // ==== Normalizadores y Filtros ====
  function normList(resp) {
    const arr = Array.isArray(resp) ? resp : (Array.isArray(resp?.data) ? resp.data : []);
    return arr.map(r => ({
      id: r.id,
      detalle: r.sugerencia || '',
      titulo: (r.sugerencia || '').split(':')[0] || 'Sugerencia',
      estado: (r.estado || 'PENDIENTE').toUpperCase(),
      usuario_id: r.usuario_id,
      creado: r.registro_instante || new Date().toISOString()
    })).filter(x => x.id).sort((a, b) => b.id - a.id);
  }

  function meFilter(list) {
    const myUid = getMyId();
    if (!myUid) {
      console.warn("No se pudo obtener el ID de usuario para filtrar sugerencias.");
      return [];
    }
    return list.filter(x => String(x.usuario_id) === String(myUid));
  }

  // ==== API Calls ====
  const fetchAll = () => API.get(SUG, '/sugerencias', { auth: true });
  const putAprobar = (id) => API.put(SUG, `/sugerencias/${id}/aprobar`, {}, { auth: true });
  const putRechazar = (id) => API.put(SUG, `/sugerencias/${id}/rechazar`, {}, { auth: true });
  async function postSuggestion(titulo, detalle) {
    const uid = getMyId();
    if (!uid) throw new Error("ID de usuario no encontrado. Por favor, inicia sesión de nuevo.");
    const payload = { usuario_id: Number(uid), sugerencia: `${titulo}: ${detalle}` };
    return await API.post(SUG, '/sugerencias', payload, { auth: true });
  }

  // ==== Renderizado ====
  function renderMine() {
    const q = mySearch.value.toLowerCase().trim();
    const f = myStatus.value.toUpperCase().trim();
    const rows = MINE.filter(r => (f === '' || r.estado === f) && (!q || r.detalle.toLowerCase().includes(q)));
    myTable.innerHTML = rows.map(r => `
      <tr class="tr">
        <td class="td">#${r.id}</td>
        <td class="td"><strong>${escapeHtml(r.titulo)}</strong></td>
        <td class="td muted">${escapeHtml(r.detalle.slice(r.titulo.length + 1).trim().substring(0, 100))}...</td>
        <td class="td">${badge(r.estado)}</td>
        <td class="td">${new Date(r.creado).toLocaleDateString()}</td>
      </tr>`).join('') || `<tr><td colspan="5" style="padding:1rem; text-align:center; opacity:0.7;">No has enviado sugerencias aún.</td></tr>`;
  }

  function renderAdmin() {
    const q = admSearch.value.toLowerCase().trim();
    const f = admStatus.value.toUpperCase().trim();
    const rows = ALL.filter(r => (f === '' || r.estado === f) && (!q || r.detalle.toLowerCase().includes(q) || String(r.usuario_id).includes(q)));
    admTable.innerHTML = rows.map(r => {
      const canAct = r.estado === 'PENDIENTE';
      return `
        <tr class="tr">
          <td class="td">#${r.id}</td>
          <td class="td muted">${escapeHtml(r.detalle.substring(0, 150))}...</td>
          <td class="td">${r.usuario_id}</td>
          <td class="td">${badge(r.estado)}</td>
          <td class="td">${new Date(r.creado).toLocaleDateString()}</td>
          <td class="td" style="text-align:right;">
            <button class="btn-xs" data-approve="${r.id}" ${!canAct && 'disabled'}>✓</button>
            <button class="btn-xs" data-reject="${r.id}" ${!canAct && 'disabled'}>×</button>
          </td>
        </tr>`;
    }).join('') || `<tr><td colspan="6" style="padding:1rem; text-align:center; opacity:0.7;">No hay sugerencias para mostrar.</td></tr>`;
  }
  
  // ==== Event Handlers ====
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const titulo = inTitulo.value.trim();
    const detalle = inDetalle.value.trim();
    if (!titulo || !detalle) return show('Completa título y detalle.', false);
    
    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = 'Enviando...';

    try {
      const res = await postSuggestion(titulo, detalle);
      form.reset();
      updateCount();
      show(`Sugerencia #${res.id} enviada correctamente.`, true);
      await loadData();
    } catch (err) {
      show(err?.payload?.detail || err.message, false);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Enviar Sugerencia';
    }
  });
  
  inDetalle.addEventListener('input', updateCount);
  
  // Filtros y actualización
  [mySearch, myStatus, admSearch, admStatus].forEach(el => el.addEventListener('input', () => {
      if (panelAdmin.style.display !== 'none') renderAdmin(); else renderMine();
  }));
  btnMyRef.addEventListener('click', loadData);
  btnAdmRef.addEventListener('click', loadData);

  // Botones de Admin
  admTable.addEventListener('click', async (ev) => {
    const btn = ev.target.closest('[data-approve], [data-reject]');
    if (!btn) return;
    const id = btn.dataset.approve || btn.dataset.reject;
    const action = btn.dataset.approve ? 'aprobar' : 'rechazar';
    if (!confirm(`¿Seguro que quieres ${action} la sugerencia #${id}?`)) return;
    
    try {
      if (action === 'aprobar') await putAprobar(id); else await putRechazar(id);
      const item = ALL.find(s => String(s.id) === id);
      if (item) item.estado = action === 'aprobar' ? 'APROBADA' : 'RECHAZADA';
      renderAdmin();
      show(`Sugerencia #${id} actualizada.`, true);
    } catch (e) {
      show(e?.payload?.detail || 'No se pudo actualizar la sugerencia.', false);
    }
  });

  // Toggle de vistas (Admin/Usuario)
  tabAdminBtn.addEventListener('click', () => { panelEnviar.style.display = 'none'; panelAdmin.style.display = 'block'; });
  btnBackToUser.addEventListener('click', () => { panelAdmin.style.display = 'none'; panelEnviar.style.display = 'block'; });

  // ==== Carga Inicial ====
  async function loadData() {
    clearMsg();
    myTable.innerHTML = `<tr><td colspan="5" style="padding:1rem; text-align:center; opacity:0.7;">Actualizando...</td></tr>`;
    try {
      const data = await fetchAll();
      ALL = normList(data);
      MINE = meFilter(ALL);
      renderMine();
      if (tabAdminBtn.style.display !== 'none') renderAdmin();
    } catch (e) {
      show('Error al cargar las sugerencias.', false);
      myTable.innerHTML = `<tr><td colspan="5" style="padding:1rem; text-align:center; color: #ef4444;">No se pudieron cargar los datos.</td></tr>`;
    }
  }

  (async function init() {
    window.Auth?.requireAuth?.();
    const u = window.Auth?.getUser?.();
    if(u) document.getElementById('userBadge').textContent = u.correo;

    if ((window.PRESTALAB?.ADMIN_EMAILS || []).includes(u?.correo)) {
        tabAdminBtn.style.display = 'block';
    }
    
    updateCount();
    await loadData();
  })();

  
  // ---------- init ----------
  window.Auth?.requireAuth?.();
  const user = window.Auth?.getUser?.();
  document.getElementById("userBadge").textContent = user?.correo || "Usuario";
  document.getElementById("btnLogout").addEventListener("click", () => window.Auth.logout());
  cargarPrestamos();

  // ---------- init ----------
  window.Auth?.requireAuth?.();
  const user = window.Auth?.getUser?.();
  document.getElementById("userBadge").textContent = user?.correo || "Usuario";
  document.getElementById("btnLogout").addEventListener("click", () => window.Auth.logout());
  cargarPrestamos();

 if (await isAdmin()) {
  tabAdminBtn.style.display = 'inline-block';
  // AÑADE ESTO:
  const nav = document.getElementById('main-nav'); // Asegúrate que el div tenga id="main-nav"
  if (nav) {
    nav.innerHTML = `
      <span class="brand">PrestaLab</span>
      <a href="dashboard.html" class="nav-link">Dashboard</a>
      <a href="admin.html" class="nav-link">Administración</a>
      <a href="reportes.html" class="nav-link">Reportes</a>
      <a href="sugerencias.html" class="nav-link active">Sugerencias</a>
    `;
  }
}

})();

