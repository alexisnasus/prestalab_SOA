// mi-perfil.js - Cargar y actualizar datos y preferencias (Servicios: REGIST y NOTIS)
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const AUTH_SERVICE = S.AUTH || 'regist';
  const NOTIS_SERVICE = S.NOTIFICATIONS || 'notis';

  // ... (DOM y Helpers sin cambios) ...
  const form = document.getElementById('profileForm');
  const elCorreo = document.getElementById('profileCorreo');
  const elNombre = document.getElementById('profileNombre');
  const elTelefono = document.getElementById('profileTelefono');
  const elState = document.getElementById('profileState');
  const btnUpdate = document.getElementById('btnUpdateProfile');
  const show = (msg, ok = false) => { /* ... */ };
  const clearMsg = () => { /* ... */ };
  const setLoading = (isLoading) => { /* ... */ };

  // Carga los datos del usuario, INCLUYENDO las preferencias
  async function loadUserProfile() {
    clearMsg();
    const userId = window.Auth?.getUserId?.();
    if (!userId) {
      show('No se pudo identificar al usuario.', false);
      return;
    }

    try {
      // Cargar datos principales de REGIST
      const userData = await API.get(AUTH_SERVICE, `/usuarios/${userId}`, { auth: true });
      if (userData) {
        elCorreo.value = userData.correo || '';
        elNombre.value = userData.nombre || '';
        elTelefono.value = userData.telefono || '';
      }

      // Cargar preferencias de NOTIS
      const prefsData = await API.get(NOTIS_SERVICE, `/preferencias/${userId}`, { auth: true });
      if (prefsData?.preferencias_notificacion) {
        const prefValue = prefsData.preferencias_notificacion;
        const radio = form.querySelector(`input[name="notifPref"][value="${prefValue}"]`);
        if (radio) radio.checked = true;
      }
    } catch (e) {
      show(e?.payload?.detail || 'No se pudieron cargar los datos del perfil.', false);
    }
  }

  // Guarda los cambios del perfil, INCLUYENDO las preferencias
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMsg();
    const userId = window.Auth?.getUserId?.();
    if (!userId) return show('Error: No se puede actualizar sin un ID de usuario.', false);

    const nombre = elNombre.value.trim();
    const telefono = elTelefono.value.trim();
    const notifPref = form.querySelector('input[name="notifPref"]:checked')?.value;

    if (!nombre) return show('El nombre no puede estar vacío.', false);
    
    setLoading(true);
    try {
      // 1. Actualizar datos principales en REGIST
      await API.put(AUTH_SERVICE, `/usuarios/${userId}`, { nombre, telefono }, { auth: true });

      // 2. Actualizar preferencias en NOTIS
      if (notifPref) {
        await API.put(NOTIS_SERVICE, `/preferencias/${userId}`, { preferencias_notificacion: parseInt(notifPref, 10) }, { auth: true });
      }
      
      show('¡Perfil actualizado correctamente!', true);

    } catch (e) {
      show(e?.payload?.detail || 'Ocurrió un error al actualizar el perfil.', false);
    } finally {
      setLoading(false);
    }
  });

 // ==== Inicialización ====
  (function init() {
    window.Auth?.requireAuth?.();
    const user = window.Auth?.getUser?.();
    document.getElementById('userBadge').textContent = user?.correo || 'Usuario';
    document.getElementById('btnLogout')?.addEventListener('click', () => window.Auth.logout());
    
    loadUserProfile();
  })();

})();