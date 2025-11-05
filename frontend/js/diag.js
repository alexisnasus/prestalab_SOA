// diag.js - Diagnóstico (CORREGIDO para el Gateway TCP)
(async function () {
  const CFG = window.PRESTALAB;
  const S = CFG.SERVICES;

  // 1) Probar el NUEVO Gateway HTTP-a-TCP (gateway.py)
  try {
    // Apuntamos a la nueva URL del Gateway definida en config.js
    const r = await fetch(CFG.GATEWAY_URL, { 
        method: 'POST', // El gateway espera POST
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service: 'diag', operation: 'ping', payload: {} }) // Enviamos un ping de prueba
    });
    
    if (r.status === 504) {
         // 504 (Gateway Timeout) significa que el Gateway SÍ respondió, pero no pudo conectar al Bus SOA.
        console.warn("[DIAG] Gateway (8001) OK, pero no pudo conectar al Bus SOA (5000). ¿El Bus está corriendo?");
    } else {
        console.log("[DIAG] Gateway (8001) responde:", r.ok ? "OK" : r.status, r.statusText);
    }

  } catch (e) {
    // Si fetch falla, el gateway (puerto 8001) ni siquiera está corriendo.
    console.error("[DIAG] Falla al contactar el Gateway HTTP-a-TCP en " + CFG.GATEWAY_URL + ". ¿El script gateway.py está corriendo?", e.message);
  }

  // 2) Probar enrutamiento completo (Frontend -> Gateway -> Bus -> Servicio 'prart')
  try {
    // ANTES: const res = await API.get(S.AUTH, "/health");
    // AHORA: Llamamos a una operación real que SÍ existe en prart/app.py
    const res = await API.getAllItems();
    
    // Si esto funciona, ¡toda la cadena está operativa!
    console.log("[DIAG] Prueba FULL-STACK (Gateway -> Bus -> prart) OK:", res);
    
  } catch (e) {
    console.error("[DIAG] Falla la prueba FULL-STACK:", e.status, e.message, e.payload || "");
  }
})();