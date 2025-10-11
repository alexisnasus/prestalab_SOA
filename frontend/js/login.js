// login.js – Manejo del formulario de login (compat con backend de demo)
(function () {
  const qs = (s) => document.querySelector(s);
  const form = qs('#loginForm');
  const email = qs('#email');
  const password = qs('#password');
  const btn = qs('#btnLogin');
  const err = qs('#loginError');
  const togglePwd = qs('#togglePwd');

  // Si ya hay sesión, ir directo al dashboard
  if (window.Auth.getToken()) {
    location.href = "dashboard.html";
    return;
  }

  function setLoading(is) {
    btn.disabled = is;
    btn.textContent = is ? 'Ingresando…' : 'Ingresar';
  }

  // Mostrar/ocultar contraseña
  togglePwd?.addEventListener('click', () => {
    password.type = password.type === 'password' ? 'text' : 'password';
    password.focus();
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    err.style.display = 'none';
    err.textContent = '';

    // Normaliza correo: minúsculas + sin espacios
    const mail = (email.value || '').toLowerCase().replace(/\s+/g, '').trim();
    const passRaw = (password.value || '').trim();

    if (!mail) {
      err.textContent = 'Ingresa tu correo institucional.';
      err.style.display = 'block';
      return;
    }
    if (!passRaw) {
      err.textContent = 'Ingresa tu contraseña.';
      err.style.display = 'block';
      return;
    }

    try {
      setLoading(true);
      await window.Auth.login(mail, passRaw);
      location.href = "dashboard.html";
    } catch (e) {
      console.error('[LOGIN] Error', e);
      let msg = 'No se pudo iniciar sesión.';
      if (e.status === 404) msg = 'Usuario no encontrado.';
      else if (e.status === 401) msg = 'Credenciales inválidas.';
      else if (e.payload && (e.payload.message || e.payload.detail)) msg = e.payload.message || e.payload.detail;
      err.textContent = msg;
      err.style.display = 'block';
    } finally {
      setLoading(false);
    }
  });
})();
