// lista-espera.js — Consultar y sumarse a lista de espera (servicio LISTA) con búsqueda por NOMBRE o ID
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  // Detecta el servicio lista sin depender del nombre exacto
  const LIST = S.WAIT || S.WAITLIST || S.LIST || S.lista;
  const CAT  = S.CATALOG; // usaremos Catálogo para resolver nombre -> id

  const state   = document.getElementById("waitState");
  const wrap    = document.getElementById("waitWrap");
  const inpId   = document.getElementById("waitItemId");
  const bJoin   = document.getElementById("btnJoin");
  const bRef    = document.getElementById("btnWaitRefresh");

  // -------- UI helpers --------
  const show = (msg, ok=false, extra=null) => {
    state.innerHTML = "";
    const p = document.createElement("div");
    p.textContent = String(msg);
    state.appendChild(p);
    if (extra) {
      const pre = document.createElement("pre");
      pre.style.whiteSpace = "pre-wrap";
      pre.style.marginTop  = "6px";
      try { pre.textContent = typeof extra === "string" ? extra : JSON.stringify(extra, null, 2); }
      catch { pre.textContent = String(extra); }
      state.appendChild(pre);
    }
    state.style.display     = "block";
    state.style.borderColor = ok ? "rgba(34,197,94,.35)" : "rgba(239,68,68,.35)";
    state.style.color       = ok ? "#22c55e"           : "#ef4444";
    state.style.background  = ok ? "rgba(34,197,94,.08)" : "rgba(239,68,68,.08)";
  };
  const clear = () => state.style.display = "none";
  const setLoading = (on=true) => wrap.innerHTML = on ? '<p style="opacity:.7">Cargando…</p>' : "";

  // -------- Parseo flexible del input (acepta ID o nombre) --------
  function parseInputToId(raw) {
    if (!raw) return { id: null, name: null };
    const m = String(raw).match(/(\d+)/);
    if (m) return { id: Number(m[1]), name: null }; // venía número (42, Ei:42, etc.)
    return { id: null, name: String(raw).trim() };   // venía un nombre
  }

  // -------- Resolver ID desde Catálogo por nombre --------
  async function resolveItemIdByName(name) {
    if (!CAT) return []; // si no está configurado Catálogo, no podemos resolver
    const candidates = [];

    // Intenta varios endpoints (ajusta según tu catálogo real)
    // 1) /items?nombre=
    try {
      const r1 = await API.get(CAT, `/items?nombre=${encodeURIComponent(name)}`, { auth: true });
      const a1 = Array.isArray(r1) ? r1 : (Array.isArray(r1?.data) ? r1.data : []);
      a1.forEach(x => candidates.push(x));
    } catch {}

    // 2) /existencias?nombre=
    try {
      const r2 = await API.get(CAT, `/existencias?nombre=${encodeURIComponent(name)}`, { auth: true });
      const a2 = Array.isArray(r2) ? r2 : (Array.isArray(r2?.data) ? r2.data : []);
      a2.forEach(x => candidates.push(x));
    } catch {}

    // 3) /catalogo/items?query=
    try {
      const r3 = await API.get(CAT, `/catalogo/items?query=${encodeURIComponent(name)}`, { auth: true });
      const a3 = Array.isArray(r3) ? r3 : (Array.isArray(r3?.data) ? r3.data : []);
      a3.forEach(x => candidates.push(x));
    } catch {}

    // Normaliza posibles formas de ID de existencia / stock
    const norm = candidates.map(x => ({
      id: Number(x?.existencia_id ?? x?.stock_id ?? x?.item_existencia_id ?? x?.id ?? NaN),
      nombre: x?.nombre ?? x?.titulo ?? x?.descripcion ?? "(sin nombre)",
      detalle: x,
    })).filter(x => Number.isFinite(x.id));

    // Quita duplicados por id
    const seen = new Set();
    const uniq = [];
    for (const c of norm) { if (!seen.has(c.id)) { seen.add(c.id); uniq.push(c); } }
    return uniq;
  }

  // -------- Render --------
  function render(list, itemId) {
    wrap.innerHTML = "";
    const rows = Array.isArray(list) ? list : [];

    const head = document.createElement("div");
    head.className = "hint";
    head.textContent = `Lista de espera para Item #${itemId}`;
    wrap.appendChild(head);

    if (!rows.length) {
      wrap.insertAdjacentHTML("beforeend", '<p style="opacity:.8">Aún no hay personas en la lista.</p>');
      return;
    }

    const ul = document.createElement("ul");
    ul.className = "bulleted";
    rows.forEach((r, idx) => {
      const li = document.createElement("li");
      li.innerHTML = `<strong>#${idx+1}</strong> • ${r?.correo ?? "usuario"} — ${r?.estado ?? "PENDIENTE"} — ${r?.registro_instante ?? ""}`;
      ul.appendChild(li);
    });
    wrap.appendChild(ul);
  }

  // -------- Consultar (acepta ID o nombre) --------
  async function consultar() {
    clear();
    setLoading(true);

    const { id, name } = parseInputToId(inpId.value);
    let itemId = id;

    try {
      if (!itemId && name) {
        const matches = await resolveItemIdByName(name);
        if (matches.length === 0) {
          setLoading(false);
          show(`No se encontraron equipos que coincidan con “${name}”.`);
          return;
        }
        if (matches.length > 1) {
          // Mostrar selector de coincidencias
          wrap.innerHTML = "<p style='opacity:.85'>Se encontraron varios resultados. Elige uno:</p>";
          const ul = document.createElement("ul");
          ul.className = "bulleted";
          matches.forEach(m => {
            const li = document.createElement("li");
            li.innerHTML = `<button class="btn btn-small">${m.nombre} (ID ${m.id})</button>`;
            li.querySelector("button").addEventListener("click", () => {
              inpId.value = `Ei:${m.id}`;
              consultar();
            });
            ul.appendChild(li);
          });
          wrap.appendChild(ul);
          show(`Se encontraron ${matches.length} coincidencias para “${name}”.`, true);
          setLoading(false);
          return;
        }
        // un solo match
        itemId = matches[0].id;
        inpId.value = `Ei:${itemId}`;
      }

      if (!itemId) {
        setLoading(false);
        show("Ingresa un ID o un nombre de equipo válido.");
        return;
      }

      // GET /lista-espera/{item_id}
      const data = await API.get(LIST, `/lista-espera/${encodeURIComponent(itemId)}`, { auth: true });
      const arr = Array.isArray(data) ? data :
                  (Array.isArray(data?.lista) ? data.lista : []);
      render(arr, itemId);
      show("Lista de espera cargada correctamente.", true);
    } catch (e) {
      let msg = "No se pudo cargar tu lista de espera.";
      if (e?.status === 405) msg = "El servicio no permite este método aún (Method Not Allowed).";
      if (e?.payload?.detail) msg += ` ${e.payload.detail}`;
      show(msg, false, e?.payload ?? e);
    } finally {
      setLoading(false);
    }
  }

  // -------- Sumarse (acepta ID o nombre) --------
  async function sumarme() {
    clear();
    setLoading(true);

    const correo = window.Auth?.getEmail?.();
    if (!correo) { setLoading(false); show("No hay sesión activa."); return; }

    const { id, name } = parseInputToId(inpId.value);
    let itemId = id;

    try {
      if (!itemId && name) {
        const matches = await resolveItemIdByName(name);
        if (matches.length === 0) { setLoading(false); show(`No se encontraron equipos para “${name}”.`); return; }
        if (matches.length > 1) {
          wrap.innerHTML = "<p style='opacity:.85'>Se encontraron varios resultados. Elige uno:</p>";
          const ul = document.createElement("ul");
          ul.className = "bulleted";
          matches.forEach(m => {
            const li = document.createElement("li");
            li.innerHTML = `<button class="btn btn-small">${m.nombre} (ID ${m.id})</button>`;
            li.querySelector("button").addEventListener("click", async () => {
              inpId.value = `Ei:${m.id}`;
              await sumarme();
            });
            ul.appendChild(li);
          });
          wrap.appendChild(ul);
          show(`Se encontraron ${matches.length} coincidencias para “${name}”.`, true);
          setLoading(false);
          return;
        }
        itemId = matches[0].id;
        inpId.value = `Ei:${itemId}`;
      }

      if (!itemId) { setLoading(false); show("Ingresa un ID o nombre de equipo válido."); return; }

      await API.post(LIST, "/lista-espera", { item_id: itemId, correo }, { auth: true });
      show("Te sumaste a la lista correctamente.", true);
      await consultar();
    } catch (e) {
      let msg = "No se pudo sumar a la lista.";
      if (e?.status === 405) msg = "El servicio no permite este método aún (Method Not Allowed).";
      if (e?.payload?.detail) msg += ` ${e.payload.detail}`;
      show(msg, false, e?.payload ?? e);
    } finally {
      setLoading(false);
    }
  }

  // -------- init --------
  window.Auth?.requireAuth?.();
  bRef?.addEventListener("click", (ev) => { ev.preventDefault(); consultar(); });
  bJoin?.addEventListener("click", (ev) => { ev.preventDefault(); sumarme(); });

  // si ya viene precargado en la URL ?item_id=42 o ?q=nombre, lo usamos
  try {
    const q = new URLSearchParams(location.search);
    const qid = q.get("item_id");
    const qname = q.get("q");
    if (qid) { inpId.value = qid; consultar(); }
    else if (qname) { inpId.value = qname; consultar(); }
  } catch {}
})();
