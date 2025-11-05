# gateway.py (CORREGIDO v2)
# Este script es el "Traductor" de HTTP (Frontend) a TCP (Bus SOA)

import socket
import json
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# --- Configuración ---
BUS_ADDRESS = ('localhost', 5000)

# --- Modelo de datos de entrada (lo que envía el Frontend) ---
class BusRequest(BaseModel):
    service: str
    operation: str
    payload: dict

# --- Inicializar la App del Gateway ---
app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- Funciones de Traducción del Protocolo ---

def format_tcp_request(service: str, operation: str, payload: dict) -> bytes:
    service_padded = service.ljust(5)[:5]
    data_str = f"{operation} {json.dumps(payload)}"
    message = f"{service_padded}{data_str}"
    message_len = len(message)
    formatted_message = f"{message_len:05d}{message}"
    print(f"[Gateway] Solicitud TCP ->: {formatted_message!r}")
    return formatted_message.encode('utf-8')

def parse_tcp_response(response: bytes) -> dict:
    """
    Parsea la respuesta NNNNNSSSSSSTDATOS.
    """
    response_str = response.decode('utf-8')
    print(f"[Gateway] Respuesta TCP <-: {response_str!r}")
    
    service_name = response_str[5:10].strip()
    status = response_str[10:12] # "OK" o "NK"
    data_json = response_str[12:] # ej: 'OK{"message":...}'
    
    # --- INICIO DE LA CORRECCIÓN ---
    # El bus parece estar duplicando el status (ej: 'OKOK{...}')
    # Si el data_json (lo que queda) empieza con el status, lo quitamos.
    if data_json.startswith(status):
        print(f"[Gateway] Detectado status duplicado ('{status}'). Removiendo...")
        data_json = data_json[len(status):] # Quita el 'OK' extra del principio
    # --- FIN DE LA CORRECCIÓN ---

    try:
        # Ahora data_json debería ser '{"message":...}'
        parsed_data = json.loads(data_json)
    except json.JSONDecodeError:
        parsed_data = {"error": "Respuesta inválida del servicio (no es JSON)", "raw": data_json}
        
    if status != "OK":
        error_message = f"Error del servicio '{service_name}': "
        if isinstance(parsed_data, dict) and parsed_data.get('error'):
            error_message += parsed_data['error']
        else:
            error_message += data_json
        
        raise HTTPException(status_code=502, detail=error_message) # 502 Bad Gateway
            
    return parsed_data

# --- Endpoint HTTP principal ---

@app.post("/route")
async def proxy_route(request: BusRequest):
    try:
        tcp_message = format_tcp_request(request.service, request.operation, request.payload)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0) 
        sock.connect(BUS_ADDRESS)
        
        sock.sendall(tcp_message)
        
        length_bytes = sock.recv(5)
        if not length_bytes:
            raise HTTPException(status_code=502, detail="Respuesta vacía del Bus SOA (no se recibió la longitud)")
            
        amount_expected = int(length_bytes.decode('utf-8'))
        
        data_received = b''
        while len(data_received) < amount_expected:
            chunk = sock.recv(amount_expected - len(data_received))
            if not chunk:
                break
            data_received += chunk
        
        sock.close()
        
        json_response = parse_tcp_response(length_bytes + data_received)
        
        return json_response
        
    except ConnectionRefusedError:
        raise HTTPException(status_code=504, detail=f"No se pudo conectar al Bus SOA TCP en {BUS_ADDRESS}. ¿Está corriendo?")
    except socket.timeout:
        raise HTTPException(status_code=504, detail="Timeout: El Bus SOA o el servicio tardaron demasiado en responder.")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error interno del Gateway: {str(e)}")

# --- Punto de entrada ---
if __name__ == "__main__":
    print(f"--- Iniciando Gateway HTTP-a-TCP en http://localhost:8001 ---")
    print(f"Este script traduce llamadas HTTP de tu frontend a llamadas TCP para el Bus SOA en {BUS_ADDRESS}")
    uvicorn.run(app, host="0.0.0.0", port=8001)