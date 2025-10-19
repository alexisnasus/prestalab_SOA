// admin.js - Lógica para el Panel de Administración (CORREGIDO)
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const AUTH_SERVICE = S.AUTH || 'regist';
  const FINES_SERVICE = S.FINES || 'multa';
  const CATALOG_SERVICE = S.CATALOG || 'prart';

  // DOM General
  const stateEl = document.getElementById('adminState');
  const tabs = document.querySelectorAll('.tab');
  const tabPanels = document.querySelectorAll('.tab-panel');

  // DOM Pestaña Usuarios
  const userTableBody = document.getElementById('userTableBody');
  const userSearch = document.getElementById('userSearch');
  
  // DOM Pestaña Solicitudes
  const solicitudesTableBody = document.getElementById('solicitudesTableBody');

  let allUsers = [];

  const show = (msg, ok = false) => {
    stateEl.textContent = msg;
    stateEl.style.display = 'block';
    stateEl.style.borderColor = ok ? 'rgba(34,197,94,0.35)' : 'rgba(239,68,68,0.35)';
    stateEl.style.color = ok ? '#22c55e' : '#ef4444';
    stateEl.style.background = ok ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)';
  };

  const checkAdmin = () => {
    const email = window.Auth?.getEmail?.();
    const adminEmails = window.PRESTALAB?.ADMIN_EMAILS || [];
    if (!adminEmails.includes(email)) {
      window.location.href = 'dashboard.html';
      return false;
    }
    return true;
  };

  // ===== GESTIÓN DE PESTAÑAS (TABS) =====
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabPanels.forEach(panel => panel.style.display = 'none');
      tabs.forEach(t => t.classList.remove('active'));
      const tabName = tab.dataset.tab;
      const activePanel = document.getElementById(`tab-content-${tabName}`);
      if (activePanel) {
        activePanel.style.display = 'block';
        tab.classList.add('active');
      }
      if (tabName === 'solicitudes' && !solicitudesTableBody.hasChildNodes()) {
        loadAllSolicitudes();
      }
    });
  });

  // ===== PESTAÑA 1: GESTIÓN DE USUARIOS =====
  function renderUsers() { /* ...código sin cambios... */ }
  async function loadUsers() { /* ...código sin cambios... */ }
  async function updateUserStatus(userId, newStatus) { /* ...código sin cambios... */ }
  userTableBody.addEventListener('change', (e) => { /* ...código sin cambios... */ });
  userSearch.addEventListener('input', renderUsers);

  // ===== PESTAÑA 2: GESTIÓN DE SOLICITUDES (LÓGICA CORREGIDA) =====
  async function loadAllSolicitudes() {
    solicitudesTableBody.innerHTML = '<tr><td colspan="6">Cargando solicitudes pendientes...</td></tr>';
    try {
      const data = await API.get(CATALOG_SERVICE, '/solicitudes', { auth: true });
      const solicitudes = (Array.isArray(data?.solicitudes) ? data.solicitudes : []).filter(s => s.estado === 'PENDIENTE');
      if (solicitudes.length === 0) {
        solicitudesTableBody.innerHTML = '<tr><td colspan="6">No hay solicitudes pendientes.</td></tr>';
        return;
      }
      solicitudesTableBody.innerHTML = '';
      solicitudes.forEach(s => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>#${s.id}</td>
          <td>Usuario ID: ${s.usuario_id}</td>
          <td>${s.articulo_nombre || '(No especificado)'}</td>
          <td>${s.tipo}</td>
          <td>${new Date(s.registro_instante).toLocaleString()}</td>
          <td class="admin-actions">
            <button class="btn btn-small" data-action="approve" data-id="${s.id}">Aprobar</button>
            <button class="btn btn-small" data-action="reject" data-id="${s.id}">Rechazar</button>
          </td>
        `;
        solicitudesTableBody.appendChild(tr);
      });
    } catch (e) {
      show('Error al cargar las solicitudes pendientes.', false);
    }
  }

  // --- FUNCIÓN DE APROBAR CORREGIDA ---
  async function aprobarSolicitud(id) {
    if (!confirm(`¿Aprobar la solicitud #${id}?`)) return;
    try {
      // LLAMAMOS AL SERVICIO CORRECTO (regist) PARA CAMBIAR EL ESTADO
      await API.put(AUTH_SERVICE, `/solicitudes/${id}/actualizar`, { estado: "APROBADA" }, { auth: true });
      show(`Solicitud #${id} aprobada.`, true);
      loadAllSolicitudes(); // Recargar la lista
    } catch (e) {
      show(`Error al aprobar la solicitud #${id}: ${e?.payload?.detail || e.message}`, false);
    }
  }

  // --- FUNCIÓN DE RECHAZAR CORREGIDA ---
  async function rechazarSolicitud(id) {
    if (!confirm(`¿Rechazar la solicitud #${id}?`)) return;
    try {
      // LLAMAMOS AL SERVICIO CORRECTO (regist) PARA CAMBIAR EL ESTADO
      await API.put(AUTH_SERVICE, `/solicitudes/${id}/actualizar`, { estado: "RECHAZADA" }, { auth: true });
      show(`Solicitud #${id} rechazada.`, true);
      loadAllSolicitudes(); // Recargar la lista
    } catch (e) {
      show(`Error al rechazar la solicitud #${id}: ${e?.payload?.detail || e.message}`, false);
    }
  }

  solicitudesTableBody.addEventListener('click', (e) => {
    const button = e.target.closest('button[data-action]');
    if (!button) return;
    const action = button.dataset.action;
    const id = button.dataset.id;
    if (action === 'approve') aprobarSolicitud(id);
    else if (action === 'reject') rechazarSolicitud(id);
  });

  // ==== INICIALIZACIÓN ====
  (function init() {
    window.Auth?.requireAuth?.();
    if (!checkAdmin()) return;
    const user = window.Auth?.getUser?.();
    document.getElementById('userBadge').textContent = user?.correo || 'Usuario';
    document.getElementById('btnLogout')?.addEventListener('click', () => window.Auth.logout());
    const nav = document.getElementById('main-nav');
    if (nav) {
      nav.innerHTML = `
        <span class="brand">PrestaLab</span>
        <a href="dashboard.html" class="nav-link">Dashboard</a>
        <a href="admin.html" class="nav-link active">Administración</a>
        <a href="reportes.html" class="nav-link">Reportes</a>
        <a href="sugerencias.html" class="nav-link">Sugerencias</a>
      `;
    }
    loadUsers();
  })();
})();