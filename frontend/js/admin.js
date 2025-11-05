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

  let allUsers = []; // Caché simple de usuarios

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
      if (tabName === 'usuarios' && !userTableBody.hasChildNodes()) {
          loadUsers(); // Cargar usuarios al hacer clic en la pestaña
      }
    });
  });

  // ===== PESTAÑA 1: GESTIÓN DE USUARIOS (IMPLEMENTADO) =====
  
  // Renderiza la tabla de usuarios desde el caché 'allUsers'
  function renderUsers() {
      const query = userSearch.value.toLowerCase().trim();
      const filteredUsers = query
          ? allUsers.filter(u => u.nombre.toLowerCase().includes(query) || u.correo.toLowerCase().includes(query))
          : allUsers;

      if (filteredUsers.length === 0) {
          userTableBody.innerHTML = '<tr><td colspan="6">No se encontraron usuarios.</td></tr>';
          return;
      }

      userTableBody.innerHTML = filteredUsers.map(user => `
          <tr>
              <td>${user.id}</td>
              <td>${user.nombre}</td>
              <td>${user.correo}</td>
              <td>${user.tipo}</td>
              <td class="admin-actions">
                  <select data-user-id="${user.id}" data-action="change-status">
                      <option value="ACTIVO" ${user.estado === 'ACTIVO' ? 'selected' : ''}>ACTIVO</option>
                      <option value="INACTIVO" ${user.estado === 'INACTIVO' ? 'selected' : ''}>INACTIVO</option>
                      <option value="SUSPENDIDO" ${user.estado === 'SUSPENDIDO' ? 'selected' : ''}>SUSPENDIDO</option>
                      <option value="DEUDOR" ${user.estado === 'DEUDOR' ? 'selected' : ''}>DEUDOR</option>
                      <option value="BLOQUEADO" ${user.estado === 'BLOQUEADO' ? 'selected' : ''}>BLOQUEADO</option>
                  </select>
              </td>
              <td>${user.registro_instante ? new Date(user.registro_instante).toLocaleDateString() : 'N/A'}</td>
          </tr>
      `).join('');
  }
  
  // Carga o busca usuarios
  async function loadUsers(query = '') {
      userTableBody.innerHTML = '<tr><td colspan="6">Cargando usuarios...</td></tr>';
      try {
          // **NOTA IMPORTANTE:**
          // Tu servicio 'regist' NO tiene una operación para buscar o listar usuarios.
          // He añadido una llamada a 'API.searchUsers' que fallará hasta que
          // 1. Añadas 'searchUsers: (payload) => sendToGateway(S.AUTH, "search_users", payload),' a tu api.js
          // 2. Añadas la operación 'search_users' a tu 'backend/services/regist/app.py'
          
          // Por ahora, simularemos la llamada
          // const data = await API.searchUsers({ query: query });
          // allUsers = data.users || [];
          
          // --- Fallback temporal ---
          // Como 'searchUsers' no existe, esto fallará.
          // Vamos a cargar solo al usuario actual como demo
          const userId = window.Auth?.getUserId();
          if (userId) {
            const user = await API.getUser({ id: userId });
            allUsers = [user]; // Solo muestra al propio admin
            show("Modo de demostración: El servicio 'regist' no puede buscar usuarios. Solo se muestra el usuario actual.", false);
          } else {
            allUsers = [];
          }
          // --- Fin del Fallback ---

          renderUsers();
      } catch (e) {
          show('Error al cargar usuarios. Es posible que la operación "search_users" falte en el backend.', false);
          userTableBody.innerHTML = '<tr><td colspan="6">Error al cargar usuarios.</td></tr>';
      }
  }

  // Actualiza el estado de un usuario
  async function updateUserStatus(userId, newStatus) {
      try {
          // Esta función SÍ existe en tu backend (update_user)
          //
          const payload = {
              id: Number(userId),
              datos: { estado: newStatus }
          };
          await API.updateUser(payload);
          show(`Estado del usuario #${userId} actualizado a ${newStatus}.`, true);
          
          // Actualiza el caché local
          const userInCache = allUsers.find(u => u.id == userId);
          if (userInCache) userInCache.estado = newStatus;

      } catch (e) {
          show(`Error al actualizar estado: ${e?.payload?.detail || e.message}`, false);
          // Recargar la lista para revertir el cambio visual
          renderUsers();
      }
  }

  userTableBody.addEventListener('change', (e) => {
      if (e.target.dataset.action === 'change-status') {
          const userId = e.target.dataset.userId;
          const newStatus = e.target.value;
          updateUserStatus(userId, newStatus);
      }
  });
  
  // Asignar el evento de búsqueda
  userSearch.addEventListener('input', renderUsers);


  // ===== PESTAÑA 2: GESTIÓN DE SOLICITUDES (CORREGIDO) =====
  async function loadAllSolicitudes() {
    solicitudesTableBody.innerHTML = '<tr><td colspan="6">Cargando solicitudes pendientes...</td></tr>';
    try {
      // ANTES: const data = await API.get(CATALOG_SERVICE, '/solicitudes', { auth: true });
      // AHORA:
      // Asumimos que una llamada sin payload trae TODAS las solicitudes (necesario para un admin)
      const data = await API.getSolicitudes({});
      
      const solicitudes = (Array.isArray(data?.solicitudes) ? data.solicitudes : []).filter(s => s.estado === 'PENDIENTE');
      
      if (solicitudes.length === 0) {
        solicitudesTableBody.innerHTML = '<tr><td colspan="6">No hay solicitudes pendientes.</td></tr>';
        return;
      }
      solicitudesTableBody.innerHTML = '';
      solicitudes.forEach(s => {
        const tr = document.createElement('tr');
        // El servicio prart/get_solicitudes devuelve 'items'
        const itemName = s.items && s.items.length > 0 ? s.items[0].nombre : '(No especificado)';
        
        tr.innerHTML = `
          <td>#${s.id}</td>
          <td>Usuario ID: ${s.usuario_id}</td>
          <td>${itemName}</td>
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
      solicitudesTableBody.innerHTML = `<tr><td colspan="6">Error: ${e?.payload?.detail || e.message}</td></tr>`;
    }
  }

  // --- FUNCIÓN DE APROBAR CORREGIDA ---
  async function aprobarSolicitud(id) {
    if (!confirm(`¿Aprobar la solicitud #${id}?`)) return;
    try {
      // ANTES: await API.put(AUTH_SERVICE, `/solicitudes/${id}/actualizar`, { estado: "APROBADA" }, { auth: true });
      // AHORA:
      const payload = { solicitud_id: Number(id), estado: "APROBADA" };
      await API.updateSolicitud(payload); // Esta función está en regist/app.py
      
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
      // ANTES: await API.put(AUTH_SERVICE, `/solicitudes/${id}/actualizar`, { estado: "RECHAZADA" }, { auth: true });
      // AHORA:
      const payload = { solicitud_id: Number(id), estado: "RECHAZADA" };
      await API.updateSolicitud(payload); // Esta función está en regist/app.py
      
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
    
    // Corrige el menú de navegación para admin
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
    
    // Carga la primera pestaña (usuarios) por defecto
    loadUsers();
  })();
})();