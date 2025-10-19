// mis-notificaciones.js - Cargar notificaciones del usuario (Servicio: NOTIS)
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const NOTIS_SERVICE = S.NOTIFICATIONS || 'notis';

  const listEl = document.getElementById('notificationList');
  const stateEl = document.getElementById('notifState');

  // Helper para mostrar mensajes de estado
  const show = (msg, ok = false) => {
    stateEl.textContent = msg;
    stateEl.style.display = 'block';
    stateEl.style.borderColor = ok ? 'rgba(34,197,94,0.35)' : 'rgba(239,68,68,0.35)';
    stateEl.style.color = ok ? '#22c55e' : '#ef4444';
    stateEl.style.background = ok ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)';
  };
  
  async function loadNotifications() {
    const userId = window.Auth?.getUserId?.();
    if (!userId) {
      show('No se pudo identificar al usuario. Por favor, inicia sesión de nuevo.', false);
      listEl.innerHTML = '<li>Error: Usuario no identificado.</li>';
      return;
    }

    listEl.innerHTML = '<li>Cargando notificaciones...</li>';
    
    try {
      // ===== NOTA IMPORTANTE =====
      // La siguiente línea está comentada porque el backend `notis` aún no tiene
      // un endpoint para OBTENER notificaciones.
      // Cuando el backend esté listo, solo debes DESCOMENTAR la siguiente línea.
      
      // const notifications = await API.get(NOTIS_SERVICE, `/notificaciones/${userId}`, { auth: true });
      
      // --- Bloque temporal mientras el backend no está listo ---
      const notifications = []; // Se devuelve un array vacío
      show('Aviso: El servicio de notificaciones aún no permite consultar mensajes.', true);
      // --- Fin del bloque temporal ---


      if (Array.isArray(notifications) && notifications.length > 0) {
        listEl.innerHTML = '';
        notifications.forEach(notif => {
          const item = document.createElement('li');
          item.className = 'notification-item';
          item.innerHTML = `
            <small>${notif.tipo} - ${new Date(notif.registro_instante).toLocaleString()}</small>
            <p style="margin: 0.25rem 0 0;">${notif.mensaje}</p>
          `;
          listEl.appendChild(item);
        });
      } else {
        listEl.innerHTML = '<li>No tienes notificaciones.</li>';
      }
    } catch (e) {
      listEl.innerHTML = '<li>Ocurrió un error al cargar las notificaciones.</li>';
      const errorMsg = e?.payload?.detail || 'El servicio de notificaciones no respondió. Es posible que el endpoint para consultar aún no esté implementado.';
      show(errorMsg, false);
    }
  }

  (function init() {
    window.Auth?.requireAuth?.();
    document.getElementById('userBadge').textContent = window.Auth?.getEmail?.() || 'Usuario';
    document.getElementById('btnLogout')?.addEventListener('click', () => window.Auth.logout());
    
    loadNotifications();
  })();
})();