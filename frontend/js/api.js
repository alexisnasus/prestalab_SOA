// api.js - Adaptador para hablar SIEMPRE con el Bus ESB vía POST /route
(function () {
  const CFG = window.PRESTALAB || {};
  const BASE = (CFG.BUS_BASE_URL || "http://localhost:8000").replace(/\/+$/,"");
  const ROUTE = (CFG.ROUTE_PATH || "/route").replace(/\/+$/,"");

  function normPath(p){ if(!p) return "/"; return p.startsWith("/") ? p : "/"+p; }

async function busFetch(service, path, opts = {}) {
  if (!service) throw new Error("api.busFetch: falta 'service'");
  const method = (opts.method || "GET").toUpperCase();

  //  Log opcional 
  if (window.PRESTALAB?.DEBUG_BUS) {
    console.debug('[BUS→] /route', {
      target_service: service,
      method,
      endpoint: normPath(path),
      payload: opts.body ?? null
    });
  }

  // Headers que viajarán al servicio
  const svcHeaders = Object.assign({}, opts.headers || {});
  if (opts.auth && window.Auth?.getToken?.()) {
    svcHeaders["Authorization"] = `Bearer ${window.Auth.getToken()}`;
  }

  const message = {
    target_service: service,
    method,
    endpoint: normPath(path),
    payload: opts.body ?? null,
    headers: Object.keys(svcHeaders).length ? svcHeaders : undefined,
    timeout: window.PRESTALAB?.DEFAULT_TIMEOUT ?? 30
  };

  const res = await fetch(`${BASE}${ROUTE}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
    body: JSON.stringify(message),
    mode: "cors",
    credentials: "omit",
  });

  const wrapper = await res.json().catch(() => ({}));

  if (window.PRESTALAB?.DEBUG_BUS) {
    console.debug('[BUS←]', { status: res.status, wrapper });
  }

  if (!wrapper.success) {
    const err = new Error(wrapper.error || res.statusText || "Error del Bus");
    err.status = wrapper.status_code || res.status;
    err.payload = wrapper;
    if (err.status === 401 || err.status === 403) { try { window.Auth?.logout?.(); } catch {} }
    throw err;
  }

  return wrapper.data;
}


  function get(s,p,o={})  { return busFetch(s,p,Object.assign({method:"GET"},o)); }
  function post(s,p,b,o={}){ return busFetch(s,p,Object.assign({method:"POST",body:b},o)); }
  function put(s,p,b,o={}) { return busFetch(s,p,Object.assign({method:"PUT",body:b},o)); }
  function del(s,p,o={})  { return busFetch(s,p,Object.assign({method:"DELETE"},o)); }

  window.API = { busFetch, get, post, put, del };
  console.log("[API] Adaptador listo (POST /route)", { BASE, ROUTE, SERVICES: CFG.SERVICES });
}

)();
