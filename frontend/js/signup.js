// signup.js — Alta de usuario vía Bus (servicio: regist)
(function () {
  const qs = (s) => document.querySelector(s);
  const form = qs('#signupForm');
  const nombre = qs('#nombre');
  const correo = qs('#correo');
  const tipo = qs('#tipo');
  const telefono = qs('#telefono');
  const password = qs('#password');
  const togglePwd = qs('#togglePwd');
  const btn = qs('#btnSignup');
  const ok = qs('#signupOk');
  const err = qs('#signupErr');

  if (window.Auth.getToken()) {
    location.href = "dashboard.html";
    return;
  }

  togglePwd?.addEventListener('click', () => {
    password.type = password.type === 'password' ? 'text' : 'password';
    password.focus();
  });

  function setLoading(is) {
    btn.disabled = is;
    btn.textContent = is ? 'Creando…' : 'Crear cuenta';
  }
  function showOk(msg) { ok.textContent = msg; ok.style.display = 'block'; err.style.display = 'none'; }
  function showErr(msg) { err.textContent = msg; err.style.display = 'block'; ok.style.display = 'none'; }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    ok.style.display = 'none';
    err.style.display = 'none';

    const mail = (correo.value || '').toLowerCase().replace(/\s+/g, '').trim();
    const name = (nombre.value || '').trim();
    const userType = (tipo.value || 'ESTUDIANTE').trim();
    const phone = (telefono.value || '').trim();
    const pass = (password.value || '').trim();

    if (!name || !mail) {
      showErr('Completa nombre y correo.');
      return;
    }
    if (!pass) {
      showErr('Debes establecer una contraseña.');
      return;
    }

    // IMPORTANTE: el servicio espera TODOS estos campos en el INSERT
    // - id: NULL para que MySQL auto-incremente
    // - telefono: NOT NULL → usa '' si viene vacío
    const payload = {
      nombre: name,
      correo: mail,
      tipo: userType,
      telefono: phone || '',             // NOT NULL en la tabla
      estado: "ACTIVO",
      preferencias_notificacion: 1,
      password: pass
    };

    try {
      setLoading(true);
      const S = window.PRESTALAB?.SERVICES || {};
      const created = await window.API.post(S.AUTH, "/usuarios", payload, { auth: false });

      const newId = created?.user?.id ?? created?.id ?? null;
      if (newId) {
        localStorage.setItem('pl_user_id', String(newId));
      }

      showOk('Cuenta creada correctamente. Te enviaremos al login…');
      setTimeout(() => location.href = "index.html", 900);
    } catch (e) {
      console.error('[SIGNUP] Error', e);
      let msg = 'No se pudo crear la cuenta.';
      if (e.status === 409) msg = 'Ese correo ya está registrado.';
      else if (e.payload && (e.payload.detail || e.payload.message || e.payload.error)) {
        msg = e.payload.detail || e.payload.message || e.payload.error;
      }
      showErr(msg);
    } finally {
      setLoading(false);
    }
  });

  
})();
