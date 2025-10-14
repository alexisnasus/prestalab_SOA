// sugerencias.js — SUGIT: enviar y administrar sugerencias (robusto con rutas/formatos alternativos)
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const SUG = S.SUGGESTIONS || S.SUGGEST || "sugit";
  const USERSVC = S.USERS || S.AUTH || S.prart;

  // --- Candidatos de endpoints (para evitar 404 del microservicio) ---
  const SUG_ENDPOINT_CANDIDATES = [
    '/sugerencias',
    '/sugerencias/',
    '/sugerencia',
    '/sugerencias/registrar',
    '/registrar'
  ];
  const SUG_LIST_CANDIDATES = [
    '/sugerencias?limit=1000',
    '/sugerencias',
    '/sugerencias/',
    '/ideas',
    '/ideas?limit=1000'
  ];

  // arma URL del bus
  function busJoin(service, path) {
    const base = (window.PRESTALAB.BUS_BASE_URL || '') + (window.PRESTALAB.ROUTE_PATH || '');
    const svc  = service.replace(/^\//,'');
    const pth  = path.startsWith('/') ? path : `/${path}`;
    return `${base}/${svc}${pth}`;
  }
  // fetch crudo (usa API.fetchRaw si existe; si no, fetch nativo)
  async function busFetchRaw(service, path, init) {
    if (API.fetchRaw) return API.fetchRaw(service, path, init);
    const url = busJoin(service, path);
    return fetch(url, init);
  }

  // DOM comunes
  const elState = document.getElementById('sugState');
  const tabs = document.querySelectorAll('.tab');
  const viewEnviar = document.getElementById('tab-enviar');
  const viewAdmin  = document.getElementById('tab-admin');
  const tabAdminBtn = document.getElementById('tabAdmin');

  // Form enviar
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

  // Estado
  let ALL = [];      // todas (admin)
  let MINE = [];     // mías
  const MAX_LEN = 800;

  // ==== Helpers UI
  const show = (msg, ok=false) => {
    elState.textContent = msg;
    elState.style.display     = "block";
    elState.style.border      = "1px solid " + (ok ? "rgba(34,197,94,.35)" : "rgba(239,68,68,.35)");
    elState.style.color       = ok ? "#22c55e" : "#ef4444";
    elState.style.background  = ok ? "rgba(34,197,94,.08)" : "rgba(239,68,68,.08)";
    elState.style.padding     = ".5rem .75rem";
    elState.style.borderRadius= ".5rem";
    elState.style.margin      = ".5rem 0";
  };
  const clearMsg = () => (elState.style.display = "none");
  const escapeHtml = (s) =>
    String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
             .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  const badge = (estado) => {
    const e = (estado||'').toUpperCase();
    if (e === 'APROBADA') return `<span class="badge b-ok">Aprobada</span>`;
    if (e === 'RECHAZADA') return `<span class="badge b-no">Rechazada</span>`;
    return `<span class="badge b-pend">Pendiente</span>`;
  };

  // ==== Admin guard por correo/rol
  async function isAdmin() {
    const email = (window.Auth?.getEmail?.() || '').toLowerCase();
    if (!email) return false;
    const wl = (window.PRESTALAB?.ADMIN_EMAILS || []).map(s => String(s).toLowerCase());
    if (wl.includes(email)) return true;

    const role = (localStorage.getItem('pl_role') || '').toUpperCase();
    if (['ADMIN','ENCARGADO','STAFF','GESTOR'].some(r => role.includes(r))) return true;

    if (!USERSVC) return false;
    try {
      const r = await API.get(USERSVC, `/usuarios/by-email?correo=${encodeURIComponent(email)}`, {auth:true});
      const u = r?.data || r;
      const tipo = String(u?.tipo || u?.rol || '').toUpperCase();
      if (['ADMIN','ENCARGADO','STAFF','GESTOR'].includes(tipo)) {
        localStorage.setItem('pl_role', tipo);
        return true;
      }
    } catch {}
    return false;
  }

  // ==== Normalizadores
  function normList(resp){
    const arr = Array.isArray(resp) ? resp
             : Array.isArray(resp?.data) ? resp.data
             : Array.isArray(resp?.items) ? resp.items : [];
    return arr.map(r => ({
      id: r?.id ?? r?.sugerencia_id,
      titulo: r?.titulo ?? r?.asunto ?? 'Sin título',
      detalle: r?.descripcion ?? r?.detalle ?? r?.mensaje ?? '',
      estado: (r?.estado ?? r?.status ?? 'PENDIENTE').toUpperCase(),
      correo: (r?.correo || r?.email || r?.usuario?.correo || '').toString().toLowerCase(),
      usuario_id: r?.usuario_id ?? r?.usuario?.id ?? null,
      creado: r?.created_at ?? r?.fecha ?? r?.creado ?? null
    })).filter(x => x.id);
  }
  function meFilter(list){
    const email = (window.Auth?.getEmail?.() || '').toLowerCase();
    const uid = window.Auth?.getUserId?.() || localStorage.getItem('pl_user_id');
    return list.filter(x => (x.correo && x.correo === email) || (uid && String(x.usuario_id) === String(uid)));
  }

  // ==== API listado (prueba rutas alternativas)
  async function fetchAll(){
    for (const p of SUG_LIST_CANDIDATES) {
      try {
        const res = await API.get(SUG, p, {auth:true});
        return normList(res);
      } catch {}
    }
    return [];
  }

  // ==== API alta: intentos progresivos (JSON + x-www-form-urlencoded) y rutas alternativas
  async function postSuggestion(titulo, detalle){
    const email = (window.Auth?.getEmail?.() || '').toLowerCase();
    const uid   = window.Auth?.getUserId?.() || localStorage.getItem('pl_user_id');
    const uidNum = /^\d+$/.test(String(uid||'')) ? Number(uid) : undefined;

    const payloads = [
      { type: 'json', body: { titulo, descripcion: detalle, correo: email, usuario_id: uidNum } },
      { type: 'json', body: { asunto: titulo, detalle, email, usuario_id: uidNum } },
      { type: 'json', body: { titulo, detalle } },
      { type: 'form', body: { titulo, descripcion: detalle, correo: email, usuario_id: uidNum ? String(uidNum) : '' } },
    ];

    let last = { status: 0, text: '', tried: [] };

    for (const path of SUG_ENDPOINT_CANDIDATES) {
      for (const p of payloads) {
        const headers = {
          ...(p.type === 'json' ? {'Content-Type':'application/json'} : {'Content-Type':'application/x-www-form-urlencoded'}),
          ...(window.Auth?.getToken ? { Authorization: `Bearer ${window.Auth.getToken()}` } : {})
        };
        const body = p.type === 'json' ? JSON.stringify(p.body) : new URLSearchParams(p.body).toString();

        try {
          const res = await busFetchRaw(SUG, path, { method:'POST', headers, body });
          const text = await res.clone().text();
          last = { status: res.status, text, tried: last.tried.concat(`${path} (${p.type})`) };

          if (res.ok) {
            let data = null; try { data = JSON.parse(text); } catch {}
            const id = data?.id || data?.sugerencia_id || data?.data?.id || data?.data?.sugerencia_id || null;
            if (window.PRESTALAB?.DEBUG_BUS) console.debug('[SUGIT OK]', path, p.type, { id, data });
            return { ok:true, id, raw: data || text };
          }

          // 404: probar siguiente combinación sin cortar
          if (res.status === 404) continue;

        } catch (e) {
          last = { status: 0, text: String(e), tried: last.tried.concat(`${path} (${p.type})`) };
        }
      }
    }

    const msg = `Fallo POST sugerencias · último estado ${last.status}.
Rutas probadas: ${last.tried.join(' | ')}
Respuesta: ${last.text.slice(0,200)}${last.text.length>200?'…':''}`;
    const err = new Error(msg);
    throw err;
  }

  async function putAprobar(id){ return API.put(SUG, `/sugerencias/${id}/aprobar`, {}, {auth:true}); }
  async function putRechazar(id){ return API.put(SUG, `/sugerencias/${id}/rechazar`, {}, {auth:true}); }

  // ==== Render
  function renderMine(){
    const q = (mySearch.value||'').toLowerCase().trim();
    const f = (myStatus.value||'').toUpperCase().trim();
    const rows = MINE.filter(r => {
      const hitQ = !q || [r.id,r.titulo,r.detalle,r.estado,r.creado].join(' ').toLowerCase().includes(q);
      const hitF = !f || r.estado === f;
      return hitQ && hitF;
    });
    myTable.innerHTML = rows.map(r => `
      <tr class="tr">
        <td class="td">#${r.id}</td>
        <td class="td"><strong>${escapeHtml(r.titulo)}</strong></td>
        <td class="td"><span class="muted">${escapeHtml(r.detalle.slice(0,120))}${r.detalle.length>120?'…':''}</span></td>
        <td class="td">${badge(r.estado)}</td>
        <td class="td">${r.creado ? new Date(r.creado).toLocaleString() : '—'}</td>
      </tr>
    `).join('') || `<tr class="tr"><td class="td" colspan="5">Sin datos.</td></tr>`;
  }

  function renderAdmin(){
    const q = (admSearch.value||'').toLowerCase().trim();
    const f = (admStatus.value||'').toUpperCase().trim();
    const rows = ALL.filter(r => {
      const hitQ = !q || [r.id,r.titulo,r.detalle,r.estado,r.correo].join(' ').toLowerCase().includes(q);
      const hitF = !f || r.estado === f;
      return hitQ && hitF;
    });
    admTable.innerHTML = rows.map(r => {
      const canAct = r.estado === 'PENDIENTE';
      return `
        <tr class="tr" data-row="${r.id}">
          <td class="td">#${r.id}</td>
          <td class="td"><strong>${escapeHtml(r.titulo)}</strong></td>
          <td class="td"><span class="muted">${escapeHtml(r.detalle.slice(0,160))}${r.detalle.length>160?'…':''}</span></td>
          <td class="td">${escapeHtml(r.correo || (r.usuario_id?`uid:${r.usuario_id}`:'—'))}</td>
          <td class="td">${badge(r.estado)}</td>
          <td class="td">${r.creado ? new Date(r.creado).toLocaleString() : '—'}</td>
          <td class="td" style="text-align:right">
            <button class="btn-xs" data-approve="${r.id}" ${canAct?'':'disabled'}>Aprobar</button>
            <button class="btn-xs" data-reject="${r.id}" ${canAct?'':'disabled'}>Rechazar</button>
          </td>
        </tr>
      `;
    }).join('') || `<tr class="tr"><td class="td" colspan="7">Sin datos.</td></tr>`;
  }

  // ==== Eventos
  tabs.forEach(t => t.addEventListener('click', () => {
    tabs.forEach(x => x.classList.remove('active'));
    t.classList.add('active');
    const key = t.getAttribute('data-tab');
    if (key === 'enviar') { viewEnviar.style.display = ''; viewAdmin.style.display = 'none'; }
    else { viewEnviar.style.display = 'none'; viewAdmin.style.display = ''; }
  }));

  function updateCount(){
    const n = (inDetalle.value||'').length;
    if (n > MAX_LEN) inDetalle.value = inDetalle.value.slice(0, MAX_LEN);
    count.textContent = `${Math.min(n,MAX_LEN)}/${MAX_LEN}`;
  }
  inDetalle.addEventListener('input', updateCount);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMsg();
    const titulo = inTitulo.value.trim();
    const detalle = inDetalle.value.trim();
    if (!titulo || !detalle) { show('Completa título y detalle.', false); return; }
    try {
      const res = await postSuggestion(titulo, detalle);
      inTitulo.value = ''; inDetalle.value = ''; updateCount();
      const suffix = res?.id ? ` (id #${res.id})` : '';
      show('¡Gracias! Tu sugerencia fue enviada' + suffix + '.', true);
      await loadMine();
      if (tabAdminBtn.style.display !== 'none') await loadAll();
    } catch (err) {
      const m = (err && err.message) ? err.message : 'No se pudo enviar la sugerencia.';
      show(m, false);
      if (window.PRESTALAB?.DEBUG_BUS) console.error('[SUGIT POST ERROR]', err);
    }
  });

  mySearch.addEventListener('input', renderMine);
  myStatus.addEventListener('change', renderMine);
  btnMyRef.addEventListener('click', () => loadMine());

  admSearch.addEventListener('input', renderAdmin);
  admStatus.addEventListener('change', renderAdmin);
  btnAdmRef.addEventListener('click', () => loadAll());

  admTable.addEventListener('click', async (ev) => {
    const ap = ev.target.closest('[data-approve]');
    const rj = ev.target.closest('[data-reject]');
    if (!ap && !rj) return;
    const id = (ap || rj).getAttribute(ap?'data-approve':'data-reject');
    if (ap && !confirm(`¿Aprobar sugerencia #${id}?`)) return;
    if (rj && !confirm(`¿Rechazar sugerencia #${id}?`)) return;
    try {
      if (ap) await putAprobar(id); else await putRechazar(id);
      const row = ALL.find(x => String(x.id) === String(id));
      if (row) row.estado = ap ? 'APROBADA' : 'RECHAZADA';
      renderAdmin();
      show(`Sugerencia #${id} ${ap?'aprobada':'rechazada'}.`, true);
    } catch (e) {
      show(e?.payload?.detail || e?.message || 'No se pudo actualizar.', false);
    }
  });

  // ==== Carga
  async function loadMine(){
    try { const all = await fetchAll(); MINE = meFilter(all); renderMine(); }
    catch { MINE = []; renderMine(); }
  }
  async function loadAll(){
    try { ALL = await fetchAll(); renderAdmin(); }
    catch { ALL = []; renderAdmin(); }
  }

  // ==== Inicio
  (async function init(){
    window.Auth?.requireAuth?.();
    try {
      const email = window.Auth?.getEmail?.();
      if (email) document.getElementById('userBadge').textContent = email;
    } catch {}
    updateCount();
    await loadMine();
    if (await isAdmin()) {
      tabAdminBtn.style.display = 'inline-block';
      await loadAll();
    }
  })();
})();
