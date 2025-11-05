// reportes.js — VERSIÓN FINAL CORREGIDA
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  const REP = S.REPORTS || S.GEREP || "gerep";
  const CATALOG = S.CATALOG || "prart"; // Para cargar sedes

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
    // El servicio gerep/app.py devuelve { "historial": [...] } o un array
    const arr = Array.isArray(resp) ? resp
              : Array.isArray(resp?.historial) ? resp.historial
              : Array.isArray(resp?.data) ? resp.data
              : Array.isArray(resp?.items) ? resp.items : [];
              
    return arr.map((r,i) => ({
      idx: i+1,
      articulo: r?.articulo || r?.item_nombre || r?.item || '—',
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
      const payload = {
          usuario_id: Number(userId),
          formato: "json"
      };
      // Llamada a la nueva API
      const json = await API.getHistorial(payload); 
      
      HIST_ALL = normalizeHist(json); // Tu lógica de normalización
      histPage = 1;
      renderHist();
      show(`Historial cargado (${HIST_ALL.length} registros).`, true);
    } catch (e) {
      HIST_ALL = [];
      renderHist();
      show(e?.payload?.detail || e?.message || 'No se pudo cargar el historial.', false);
    }
  }

  // Descargas (CSV/PDF) - ¡MODIFICADO!
  async function downloadHist(userId, format){
    clearMsg();
    show(`Generando ${format.toUpperCase()}...`, true);
    try {
      const payload = {
        usuario_id: Number(userId),
        formato: format
      };
      // Llamar a la API
      const data = await API.getHistorial(payload);

      // El servicio 'gerep' devuelve JSON con 'filename' y 'content' (base64)
      //
      if (data && data.content && data.filename) {
        // Crear un link de descarga desde el base64
        const link = document.createElement('a');
        const mimeType = format === 'pdf' ? 'application/pdf' : 'text/csv';
        link.href = `data:${mimeType};base64,${data.content}`;
        link.download = data.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        clearMsg();
      } else {
        throw new Error("La respuesta del servicio no tiene el formato de archivo esperado.");
      }
    } catch (e) {
      show(e?.payload?.detail || e?.message || 'No se pudo descargar el archivo.', false);
    }
  }

  // ==== CIRCULACIÓN
  
  // ¡MODIFICADO! para adaptarse a lo que 'gerep/app.py' realmente devuelve
  function normalizeCirc(resp){
     // El servicio 'gerep' devuelve un objeto, no un array:
     // { "metricas": { "rotacion_total": ..., "morosidad_porcentaje": ..., "danos_reportados": ... } }
     //
     
     const metrics = resp?.metricas;
     if (metrics) {
        // Adaptamos la salida para que coincida con las columnas de la tabla HTML
        return [
          { categoria: 'Rotación Total (Préstamos)', prestamos: metrics.rotacion_total, usuarios: 'N/A', rotacion: 'N/A' },
          { categoria: 'Morosidad (%)', prestamos: metrics.morosidad_porcentaje, usuarios: 'N/A', rotacion: 'N/A' },
          { categoria: 'Daños Reportados', prestamos: metrics.danos_reportados, usuarios: 'N/A', rotacion: 'N/A' },
        ];
     }
     return []; // Devuelve vacío si la respuesta no es la esperada
  }

  // ¡MODIFICADO!
  async function loadCirc(periodo, sedeId){
    clearMsg();
    circTable.innerHTML = `<tr class="tr"><td class="td" colspan="4">Cargando…</td></tr>`;
    try {
      const payload = {
        periodo: periodo,
        sede_id: Number(sedeId) // El servicio espera sede_id
      };
      // Llamada a la nueva API
      const data = await API.getReporteCirculacion(payload);
      
      const rows = normalizeCirc(data); // Tu lógica de normalización
      
      // Ajustamos las columnas para que coincidan con la nueva data
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

  // ¡MODIFICADO!
  async function loadSedes(){
    const opts = [];
    try {
      // El servicio 'prart' NO tiene un endpoint '/sedes'.
      // Esta llamada fallará (lo cual está bien, activará el 'catch {}').
      const r = await API.searchItems({ "nombre": "dummy_para_probar_api" }); // Usamos una llamada que sí exista
    } catch {}
    
    // Como la llamada a la API fallará o no devolverá sedes, se usará este fallback.
    // Usamos los nombres de tu archivo 'seed_data.sql'
    if (!opts.length) {
        opts.push({id:'1', nombre:'FIC_LABORATORIO_01 (Sede 1)'});
        opts.push({id:'2', nombre:'FIC_LABORATORIO_02 (Sede 2)'});
        opts.push({id:'3', nombre:'FIC_LABORATORIO_03 (Sede 3)'});
    }
    circSede.innerHTML = opts.map(o => `<option value="${escapeHtml(o.id)}">${escapeHtml(o.nombre)}</option>`).join('');
  }

  // ==== eventos (Sin cambios)
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

  // ==== inicio (LIMPIO Y CORRECTO)
  (function init(){
    window.Auth?.requireAuth?.();
    
    // badge usuario
    try {
      const user = window.Auth?.getUser?.(); // Obtenido de auth.js
      if (user && user.correo) {
          document.getElementById('userBadge').textContent = user.correo;
      } else {
          // Fallback por si getUser() no está listo
          const email = window.Auth?.getEmail?.();
          if (email) document.getElementById('userBadge').textContent = email;
      }
    } catch {}
    
    // Botón de Logout
    document.getElementById('btnLogout')?.addEventListener('click', () => window.Auth.logout());

    // tab inicial
    const now = new Date(); 
    circPeriodo.value = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`;
    loadSedes();
    
  })();
  
})(); // Cierre del IIFE principal