// mi-perfil.js - (CORREGIDO PARA NUEVA API)
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const AUTH_SERVICE = S.AUTH || 'regist';
  const NOTIS_SERVICE = S.NOTIFICATIONS || 'notis';

  // --- DOM y Helpers (Sin cambios) ---
  const form = document.getElementById('profileForm');
  const elCorreo = document.getElementById('profileCorreo');
  const elNombre = document.getElementById('profileNombre');
  const elTelefono = document.getElementById('profileTelefono');
  const elState = document.getElementById('profileState');
  const btnUpdate = document.getElementById('btnUpdateProfile');
  
  // (Asumimos que tus helpers 'show', 'clearMsg' y 'setLoading' están definidos aquí)
  // --- INICIO Helpers (copiados de tu ejemplo) ---
  const show = (msg, ok = false) => {
    elState.textContent = msg;
    elState.style.display = 'block';
    elState.style.borderColor = ok ? 'rgba(34,197,94,0.35)' : 'rgba(239,68,68,0.35)';
    elState.style.color = ok ? '#22c55e' : '#ef4444';
    elState.style.background = ok ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)';
  };
  const clearMsg = () => { elState.style.display = 'none'; };
  const setLoading = (isLoading) => {
    btnUpdate.disabled = isLoading;
    btnUpdate.textContent = isLoading ? 'Guardando...' : 'Guardar Cambios';
  };
  // --- FIN Helpers ---


  // --- Carga los datos (CORREGIDO) ---
  async function loadUserProfile() {
    clearMsg();
    const userId = window.Auth?.getUserId?.();
    if (!userId) {
      show('No se pudo identificar al usuario.', false);
      return;
    }

    try {
      // --- CAMBIO 1 ---
      // ANTES: const userData = await API.get(AUTH_SERVICE, `/usuarios/${userId}`, { auth: true });
      // AHORA:
      const userData = await API.getUser({ id: userId });
      
      if (userData) {
        elCorreo.value = userData.correo || '';
        elNombre.value = userData.nombre || '';
        elTelefono.value = userData.telefono || '';
      }

      // --- CAMBIO 2 ---
      // ANTES: const prefsData = await API.get(NOTIS_SERVICE, `/preferencias/${userId}`, { auth: true });
      // AHORA:
      const prefsData = await API.getPreferencias({ usuario_id: userId });

      if (prefsData?.preferencias_notificacion) {
        const prefValue = prefsData.preferencias_notificacion;
        const radio = form.querySelector(`input[name="notifPref"][value="${prefValue}"]`);
        if (radio) radio.checked = true;
      }
    } catch (e) {
      show(e?.payload?.detail || 'No se pudieron cargar los datos del perfil.', false);
    }
  }

  // --- Guarda los cambios (CORREGIDO) ---
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMsg();
    const userId = window.Auth?.getUserId?.();
    if (!userId) return show('Error: No se puede actualizar sin un ID de usuario.', false);

    const nombre = elNombre.value.trim();
    const telefono = elTelefono.value.trim();
    const notifPrefInput = form.querySelector('input[name="notifPref"]:checked');
    const notifPref = notifPrefInput ? parseInt(notifPrefInput.value, 10) : null;

    if (!nombre) return show('El nombre no puede estar vacío.', false);
    
    setLoading(true);
    try {
      // --- CAMBIO 3 ---
      // 1. Actualizar datos principales en REGIST
      // ANTES: await API.put(AUTH_SERVICE, `/usuarios/${userId}`, { nombre, telefono }, { auth: true });
      // AHORA:
      const userPayload = {
        id: userId,
        datos: { nombre: nombre, telefono: telefono } // El servicio 'regist' espera un objeto 'datos'
      };
      await API.updateUser(userPayload);

      // --- CAMBIO 4 ---
      // 2. Actualizar preferencias en NOTIS
      if (notifPref !== null) {
        // ANTES: await API.put(NOTIS_SERVICE, `/preferencias/${userId}`, { preferencias_notificacion: parseInt(notifPref, 10) }, { auth: true });
        // AHORA:
        const notisPayload = {
          usuario_id: userId,
          preferencias_notificacion: notifPref
        };
        await API.updatePreferencias(notisPayload);
      }
      
      show('¡Perfil actualizado correctamente!', true);

    } catch (e) {
      show(e?.payload?.detail || e.message || 'Ocurrió un error al actualizar el perfil.', false);
    } finally {
      setLoading(false);
    }
  });

 // ==== Inicialización (Sin cambios) ====
  (function init() {
    window.Auth?.requireAuth?.();
    const user = window.Auth?.getUser?.();
    document.getElementById('userBadge').textContent = user?.correo || 'Usuario';
    document.getElementById('btnLogout')?.addEventListener('click', () => window.Auth.logout());
    
    loadUserProfile();
  })();

})();