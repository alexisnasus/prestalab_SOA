# gateway.py (VERSIÓN ROBUSTA FINAL)
import socket
import json
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# --- Configuración ---
BUS_ADDRESS = ('localhost', 5000)

# --- Modelo de datos ---
class BusRequest(BaseModel):
    service: str
    operation: str
    payload: dict

# --- App ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- Helpers ---
def format_tcp_request(service: str, operation: str, payload: dict) -> bytes:
    service_padded = service.ljust(5)[:5]
    data_str = f"{operation} {json.dumps(payload)}"
    message = f"{service_padded}{data_str}"
    message_len = len(message)
    formatted_message = f"{message_len:05d}{message}"
    print(f"[Gateway] Solicitud TCP ->: {formatted_message!r}")
    return formatted_message.encode('utf-8')

def parse_tcp_response(response: bytes) -> dict:
    try:
        response_str = response.decode('utf-8')
    except UnicodeDecodeError:
        # Fallback para datos binarios (como PDFs) si los hubiera
        response_str = response.decode('latin-1')

    print(f"[Gateway] Respuesta TCP <-: {response_str!r}")
    
    # Protocolo: NNNNNSSSSSSTDATOS
    # NNNNN (0-5), SSSSS (5-10), ST (10-12), DATOS (12-end)
    service_name = response_str[5:10].strip()
    status = response_str[10:12]     # ej: "OK" o "NK"
    data_raw = response_str[12:]     # ej: 'OK{"message":...}' o '{"message":...}'
    
    # --- CORRECCIÓN CRÍTICA PARA EL "DOUBLE OK" ---
    # Si los datos empiezan con el mismo status (ej. OKOK...), lo quitamos.
    if data_raw.startswith(status):
        print(f"[Gateway] ¡AVISO! Status duplicado detectado ('{status}'). Corrigiendo...")
        data_raw = data_raw[len(status):]
    # -----------------------------------------------

    try:
        parsed_data = json.loads(data_raw)
    except json.JSONDecodeError as e:
        print(f"[Gateway] Error al parsear JSON: {e}")
        # Si falla, devolvemos el texto crudo para depuración
        parsed_data = {"error": "Respuesta no es JSON válido", "raw_response": data_raw}

    if status == "NK":
        # Extraer mensaje de error si existe
        error_msg = parsed_data.get("error", data_raw) if isinstance(parsed_data, dict) else data_raw
        print(f"[Gateway] Error del servicio {service_name}: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

    return parsed_data

# --- Endpoint ---
@app.post("/route")
async def proxy_route(request: BusRequest):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(15.0) 
    try:
        sock.connect(BUS_ADDRESS)
        sock.sendall(format_tcp_request(request.service, request.operation, request.payload))
        
        # Leer longitud (5 bytes)
        length_bytes = sock.recv(5)
        if not length_bytes:
             raise HTTPException(status_code=502, detail="El Bus SOA cerró la conexión inesperadamente.")
        amount_expected = int(length_bytes.decode('utf-8'))
        
        # Leer datos completos
        data_received = b''
        while len(data_received) < amount_expected:
            chunk = sock.recv(min(4096, amount_expected - len(data_received)))
            if not chunk: break
            data_received += chunk
            
        return parse_tcp_response(length_bytes + data_received)

    except ConnectionRefusedError:
        raise HTTPException(status_code=503, detail="No se pudo conectar al Bus SOA (localhost:5000). ¿Está encendido?")
    except socket.timeout:
        raise HTTPException(status_code=504, detail="Timeout esperando respuesta del Bus SOA.")
    except Exception as e:
        # Si ya es HTTPException, lo dejamos pasar
        if isinstance(e, HTTPException): raise e
        print(f"[Gateway] Error interno: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        sock.close()

if __name__ == "__main__":
    print("--- Gateway HTTP-TCP activo en puerto 8001 ---")
    uvicorn.run(app, host="0.0.0.0", port=8001)