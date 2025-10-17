// reportes.js — GEREP: historial por usuario + circulación por sede
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const REP = S.REPORTS || S.GEREP || "gerep";
  const CATALOG = S.CATALOG || "prart";

  // DOM
  const elState = document.getElementById('repState');

  // Tabs
  const tabs = document.querySelectorAll('.tab');
  const viewHist = document.getElementById('tab-hist');
  const viewCirc = document.getElementById('tab-circ');

  // Historial
  const histUserId = document.getElementById('histUserId');
  const btnHistMy = document.getElementById('btnHistMy');
  const histFilter = document.getElementById('histFilter');
  const btnHistBuscar = document.getElementById('btnHistBuscar');
  const btnHistCSV = document.getElementById('btnHistCSV');
  const btnHistPDF = document.getElementById('btnHistPDF');
  const histTable = document.getElementById('histTable');
  const histPager = document.getElementById('histPager');

  // Circulación
  const circPeriodo = document.getElementById('circPeriodo');
  const circSede = document.getElementById('circSede');
  const btnCircConsultar = document.getElementById('btnCircConsultar');
  const circTable = document.getElementById('circTable');
  const circNote = document.getElementById('circNote');

  // Estado local
  let HIST_ALL = [];
  let histPage = 1;
  const HIST_PAGE_SIZE = 20;

  // ==== helpers UI
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

  // ==== Tabs
  tabs.forEach(t => t.addEventListener('click', () => {
    tabs.forEach(x => x.classList.remove('active'));
    t.classList.add('active');
    const key = t.getAttribute('data-tab');
    if (key === 'hist') { viewHist.style.display = ''; viewCirc.style.display = 'none'; }
    else { viewHist.style.display = 'none'; viewCirc.style.display = ''; }
  }));

  // ==== HISTORIAL
  function normalizeHist(resp){
    const arr = Array.isArray(resp) ? resp
              : Array.isArray(resp?.data) ? resp.data
              : Array.isArray(resp?.items) ? resp.items : [];
    return arr.map((r,i) => ({
      idx: i+1,
      articulo: r?.articulo || r?.item_nombre || r?.equipo || r?.item?.nombre || '—',
      item: r?.item_id ?? r?.item?.id ?? '—',
      desde: r?.fecha_prestamo || r?.desde || r?.inicio || r?.created_at || '—',
      hasta: r?.fecha_devolucion || r?.hasta || r?.fin || r?.updated_at || '—',
      estado: r?.estado || r?.status || '—',
    }));
  }

  function renderHist(){
    const q = (histFilter.value||'').toLowerCase().trim();
    const filtered = q
      ? HIST_ALL.filter(r =>
          [r.articulo, r.item, r.desde, r.hasta, r.estado]
           .join(' ').toLowerCase().includes(q))
      : HIST_ALL.slice();

    const total = filtered.length;
    const start = (histPage-1)*HIST_PAGE_SIZE;
    const end = start + HIST_PAGE_SIZE;
    const pageItems = filtered.slice(start, end);

    histTable.innerHTML = pageItems.map(r => `
      <tr class="tr">
        <td class="td">${r.idx}</td>
        <td class="td"><strong>${escapeHtml(r.articulo)}</strong> <span class="muted">· ítem:${escapeHtml(r.item)}</span></td>
        <td class="td">${escapeHtml(formatDate(r.desde))}</td>
        <td class="td">${escapeHtml(formatDate(r.hasta))}</td>
        <td class="td">${escapeHtml(r.estado)}</td>
      </tr>
    `).join('') || `<tr class="tr"><td class="td" colspan="5">Sin datos.</td></tr>`;

    const pages = Math.max(1, Math.ceil(total / HIST_PAGE_SIZE));
    histPager.innerHTML = `Mostrando ${Math.min(end,total)} de ${total} registros · Página ${histPage}/${pages}` +
      (pages>1 ? ` — <button class="btn btn-xs" ${histPage<=1?'disabled':''} data-pg="prev">«</button>
                  <button class="btn btn-xs" ${histPage>=pages?'disabled':''} data-pg="next">»</button>` : '');

    histPager.onclick = (e) => {
      const b = e.target.closest('[data-pg]'); if (!b) return;
      const dir = b.getAttribute('data-pg');
      histPage = Math.min(pages, Math.max(1, histPage + (dir==='next'?1:-1)));
      renderHist();
    };
  }

  function formatDate(d){
    if (!d) return '—';
    try { return new Date(d).toLocaleString(); } catch { return String(d); }
  }

  async function loadHist(userId){
    clearMsg();
    histTable.innerHTML = '<tr class="tr"><td class="td" colspan="5">Cargando…</td></tr>';
    try {
      const json = await API.get(REP, `/usuarios/${encodeURIComponent(userId)}/historial?formato=json`, {auth:true});
      HIST_ALL = normalizeHist(json);
      histPage = 1;
      renderHist();
      show(`Historial cargado (${HIST_ALL.length} registros).`, true);
    } catch (e) {
      HIST_ALL = [];
      renderHist();
      show(e?.payload?.detail || e?.message || 'No se pudo cargar el historial.', false);
    }
  }

  // Descargas (CSV/PDF) usando helper de api.js
  async function downloadHist(userId, format){
    try {
      const path = `/usuarios/${encodeURIComponent(userId)}/historial?formato=${format}`;
      const fname = `historial_${userId}.${format}`;
      await API.download(REP, path, fname, {auth:true});
    } catch (e) {
      show('No se pudo descargar el archivo.', false);
    }
  }

  // ==== CIRCULACIÓN
  function normalizeCirc(resp){
    const arr = Array.isArray(resp) ? resp
              : Array.isArray(resp?.data) ? resp.data
              : Array.isArray(resp?.items) ? resp.items : (resp ? [resp] : []);
    // Intento de mapeo común
    return arr.map(r => ({
      categoria: r?.categoria || r?.tipo || r?.familia || 'Total',
      prestamos: Number(r?.prestamos ?? r?.count ?? r?.cantidad ?? 0),
      usuarios: Number(r?.usuarios_unicos ?? r?.usuarios ?? 0),
      rotacion: Number(r?.rotacion ?? r?.ratio ?? 0)
    }));
  }

  async function loadCirc(periodo, sedeId){
    clearMsg();
    circTable.innerHTML = `<tr class="tr"><td class="td" colspan="4">Cargando…</td></tr>`;
    try {
      const qs = `?periodo=${encodeURIComponent(periodo)}&sede=${encodeURIComponent(sedeId)}`;
      const data = await API.get(REP, `/reportes/circulacion${qs}`, {auth:true});
      const rows = normalizeCirc(data);
      circTable.innerHTML = rows.map(r => `
        <tr class="tr">
          <td class="td">${escapeHtml(r.categoria)}</td>
          <td class="td">${r.prestamos}</td>
          <td class="td">${r.usuarios}</td>
          <td class="td">${r.rotacion}</td>
        </tr>
      `).join('') || `<tr class="tr"><td class="td" colspan="4">Sin datos.</td></tr>`;
      circNote.textContent = `Periodo ${periodo} · Sede ${sedeId}`;
      show(`Reporte de circulación listo.`, true);
    } catch (e) {
      circTable.innerHTML = `<tr class="tr"><td class="td" colspan="4">Error al cargar.</td></tr>`;
      show(e?.payload?.detail || e?.message || 'No se pudo cargar el reporte de circulación.', false);
    }
  }

  async function loadSedes(){
    // intenta endpoint de sedes; si no existe, fallback
    const opts = [];
    try {
      const r = await API.get(CATALOG, '/sedes?limit=100', {auth:true});
      const arr = Array.isArray(r?.data) ? r.data : Array.isArray(r) ? r : [];
      arr.forEach(s => opts.push({id: s.id ?? s.codigo ?? s.slug, nombre: s.nombre ?? s.alias ?? `Sede ${s.id}`}));
    } catch {}
    if (!opts.length) opts.push({id:'1', nombre:'Casa Central'},{id:'2', nombre:'San Carlos'},{id:'3', nombre:'Peñalolén'});
    circSede.innerHTML = opts.map(o => `<option value="${escapeHtml(o.id)}">${escapeHtml(o.nombre)}</option>`).join('');
  }

  // ==== eventos
  btnHistMy.addEventListener('click', () => {
    const uid = window.Auth?.getUserId?.() || localStorage.getItem('pl_user_id');
    if (uid) histUserId.value = uid;
  });
  btnHistBuscar.addEventListener('click', () => {
    const uid = (histUserId.value||'').trim();
    if (!uid) { show('Indica un ID de usuario.', false); return; }
    loadHist(uid);
  });
  histFilter.addEventListener('input', () => { renderHist(); });
  btnHistCSV.addEventListener('click', () => {
    const uid = (histUserId.value||'').trim();
    if (!uid) { show('Indica un ID de usuario.', false); return; }
    downloadHist(uid,'csv');
  });
  btnHistPDF.addEventListener('click', () => {
    const uid = (histUserId.value||'').trim();
    if (!uid) { show('Indica un ID de usuario.', false); return; }
    downloadHist(uid,'pdf');
  });

  btnCircConsultar.addEventListener('click', () => {
    const per = (circPeriodo.value||'').trim();
    const sede = (circSede.value||'').trim();
    if (!per || !sede) { show('Selecciona periodo y sede.', false); return; }
    loadCirc(per, sede);
  });

  // ==== inicio
  (function init(){
    window.Auth?.requireAuth?.();
    // tab inicial
    const now = new Date(); 
    circPeriodo.value = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`;
    loadSedes();
    // badge usuario
    try {
      const email = window.Auth?.getEmail?.();
      if (email) document.getElementById('userBadge').textContent = email;
    } catch {}

    
  // ---------- init ----------
  window.Auth?.requireAuth?.();
  const user = window.Auth?.getUser?.();
  document.getElementById("userBadge").textContent = user?.correo || "Usuario";
  document.getElementById("btnLogout").addEventListener("click", () => window.Auth.logout());
  cargarPrestamos();
  })();

  if (await isAdmin()) {
  tabAdminBtn.style.display = 'inline-block';
  // AÑADE ESTO:
  const nav = document.getElementById('main-nav'); // Asegúrate que el div tenga id="main-nav"
  if (nav) {
    nav.innerHTML = `
      <span class="brand">PrestaLab</span>
      <a href="dashboard.html" class="nav-link">Dashboard</a>
      <a href="admin.html" class="nav-link">Administración</a>
      <a href="reportes.html" class="nav-link">Reportes</a>
      <a href="sugerencias.html" class="nav-link active">Sugerencias</a>
    `;
  }
}
})();
