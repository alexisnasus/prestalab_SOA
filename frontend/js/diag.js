// diag.js - Diagnóstico para Paso 1
(async function () {
  const CFG = window.PRESTALAB;
  const S = CFG.SERVICES;

  // 1) Probar /health del Bus (si existe)
  try {
    const r = await fetch(CFG.BUS_BASE_URL.replace(/\/+$/,"") + "/health", { mode: "cors" });
    console.log("[DIAG] BUS /health:", r.ok ? "OK" : r.status, r.statusText);
  } catch (e) {
    console.warn("[DIAG] BUS /health no disponible (no es grave):", e.message);
  }

  // 2) Probar enrutamiento a AUTH /health vía /route
  try {
    const res = await API.get(S.AUTH, "/health");
    console.log("[DIAG] /route -> AUTH /health OK:", res);
  } catch (e) {
    console.error("[DIAG] Falla /route AUTH /health:", e.status, e.message, e.payload || "");
  }
})();
