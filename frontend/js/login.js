// login.js
(function () {
  const form = document.getElementById('loginForm');
  const email = document.getElementById('email');
  const password = document.getElementById('password');
  const btn = document.getElementById('btnLogin');
  const err = document.getElementById('loginError');
  const togglePwd = document.getElementById('togglePwd');

  if (window.Auth.getToken()) { location.href = "dashboard.html"; return; }

  togglePwd?.addEventListener('click', () => {
    password.type = password.type === 'password' ? 'text' : 'password';
    password.focus();
  });

  const setLoading = (is) => { btn.disabled = is; btn.textContent = is ? 'Ingresando…' : 'Ingresar'; };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    err.style.display = 'none'; err.textContent = '';

    const correo = (email.value || '').toLowerCase().trim();
    const pass   = (password.value || '').trim();
    if (!correo || !pass) {
      err.textContent = 'Completa correo y contraseña.'; err.style.display = 'block'; return;
    }

    setLoading(true);
    try {
      await window.Auth.login(correo, pass);
      location.href = "dashboard.html";
    } catch (ex) {
      console.error('[LOGIN] Error', ex);
      let msg = 'No se pudo iniciar sesión.';
      if (ex.status === 401) msg = 'Credenciales inválidas.';
      else if (ex.status === 404) msg = 'Usuario no encontrado.';
      else if (ex.payload && (ex.payload.detail || ex.payload.message || ex.payload.error)) {
        msg = ex.payload.detail || ex.payload.message || ex.payload.error;
      }
      err.textContent = msg; err.style.display = 'block';
    } finally {
      setLoading(false);
    }
  });
})();
