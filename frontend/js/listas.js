// lista-espera.js — Consultar y sumarse a lista de espera (servicio LISTA)
(function () {
  const S = window.PRESTALAB?.SERVICES || {};
  // Detecta el servicio lista sin depender del nombre exacto
  const LIST = S.WAIT || S.WAITLIST || S.LIST || S.lista;

  const state   = document.getElementById("waitState");
  const wrap    = document.getElementById("waitWrap");
  const inpId   = document.getElementById("waitItemId");
  const bJoin   = document.getElementById("btnJoin");
  const bRef    = document.getElementById("btnWaitRefresh");

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

  // Normaliza el campo ingresado (acepta "42", "Ei:42", "ei-42", etc.)
  function parseItemId(raw) {
    if (!raw) return null;
    const m = String(raw).match(/(\d+)/);
    return m ? Number(m[1]) : null;
  }

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

  async function consultar() {
    clear();
    setLoading(true);

    const itemId = parseItemId(inpId.value);
    if (!itemId) {
      setLoading(false);
      show("Ingresa un Item ID válido (por ejemplo 42 o Ei:42).");
      return;
    }

    try {
      // GET /lista-espera/{item_id}
      const data = await API.get(LIST, `/lista-espera/${encodeURIComponent(itemId)}`, { auth: true });
      // tolerante: el servicio puede devolver { item_id, lista:[...] } o array directo
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

  async function sumarme() {
    clear();
    setLoading(true);

    const correo = window.Auth?.getEmail?.();
    if (!correo) {
      setLoading(false);
      show("No hay sesión activa.");
      return;
    }
    const itemId = parseItemId(inpId.value);
    if (!itemId) {
      setLoading(false);
      show("Ingresa un Item ID válido (por ejemplo 42 o Ei:42).");
      return;
    }

    try {
      // POST /lista-espera  { item_id, correo }
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

  // init
  window.Auth?.requireAuth?.();
  bRef?.addEventListener("click", (ev) => { ev.preventDefault(); consultar(); });
  bJoin?.addEventListener("click", (ev) => { ev.preventDefault(); sumarme(); });

  // si ya viene precargado en la URL ?item_id=42, lo usamos
  try {
    const q = new URLSearchParams(location.search);
    const qid = q.get("item_id");
    if (qid) {
      inpId.value = qid;
      consultar();
    }
  } catch {}

})();
