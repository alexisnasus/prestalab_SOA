// mi-perfil.js - Cargar y actualizar datos de usuario (Servicio: REGIST)
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const AUTH_SERVICE = S.AUTH || 'regist';

  // DOM
  const form = document.getElementById('profileForm');
  const elCorreo = document.getElementById('profileCorreo');
  const elNombre = document.getElementById('profileNombre');
  const elTelefono = document.getElementById('profileTelefono');
  const elState = document.getElementById('profileState');
  const btnUpdate = document.getElementById('btnUpdateProfile');

  // ==== Helpers UI ====
  const show = (msg, ok = false) => {
    elState.textContent = msg;
    elState.style.display = 'block';
    elState.style.borderColor = ok ? 'rgba(34,197,94,0.35)' : 'rgba(239,68,68,0.35)';
    elState.style.color = ok ? '#22c55e' : '#ef4444';
    elState.style.background = ok ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)';
  };
  const clearMsg = () => (elState.style.display = 'none');
  const setLoading = (isLoading) => {
    btnUpdate.disabled = isLoading;
    btnUpdate.textContent = isLoading ? 'Guardando...' : 'Guardar Cambios';
  };

  // ==== Lógica Principal ====
  
  // Carga los datos del usuario al iniciar la página
  async function loadUserProfile() {
    clearMsg();
    const userId = window.Auth?.getUserId?.();

    if (!userId) {
      show('No se pudo identificar al usuario. Por favor, inicia sesión de nuevo.', false);
      return;
    }

    try {
      // Usamos GET /usuarios/{id} del servicio REGIST
      const userData = await API.get(AUTH_SERVICE, `/usuarios/${userId}`, { auth: true });

      if (userData) {
        elCorreo.value = userData.correo || '';
        elNombre.value = userData.nombre || '';
        elTelefono.value = userData.telefono || '';
      }
    } catch (e) {
      show(e?.payload?.detail || 'No se pudieron cargar los datos del perfil.', false);
    }
  }

  // Maneja el envío del formulario para actualizar los datos
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMsg();
    
    const userId = window.Auth?.getUserId?.();
    if (!userId) {
      show('Error: No se puede actualizar sin un ID de usuario.', false);
      return;
    }

    const nombre = elNombre.value.trim();
    const telefono = elTelefono.value.trim();

    if (!nombre) {
      show('El nombre no puede estar vacío.', false);
      return;
    }
    
    // El payload solo debe contener los campos que se pueden modificar
    const payload = {
      nombre,
      telefono
    };

    setLoading(true);
    try {
      // Usamos PUT /usuarios/{id} del servicio REGIST
      await API.put(AUTH_SERVICE, `/usuarios/${userId}`, payload, { auth: true });
      show('¡Perfil actualizado correctamente!', true);

      // Opcional: Actualizar el objeto de usuario en localStorage si es necesario
      const user = window.Auth?.getUser?.();
      if (user) {
        user.nombre = nombre;
        localStorage.setItem('pl_user', JSON.stringify(user));
      }

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