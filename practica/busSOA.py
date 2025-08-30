import socket
import threading

class SOABus:
    def __init__(self):
        self.services = {}  # Diccionario para almacenar servicios registrados
        self.clients = {}   # Diccionario para almacenar clientes conectados
        self.client_service_map = {}  # Mapear clientes con los servicios que solicitan
        
    def handle_client(self, client_socket, client_address):
        print(f"Nueva conexión desde {client_address}")
        
        try:
            while True:
                # Recibir longitud del mensaje
                length_data = client_socket.recv(5)
                if not length_data:
                    break
                    
                message_length = int(length_data.decode())
                print(f"Longitud esperada del mensaje: {message_length}")
                
                # Recibir mensaje completo
                message = b''
                while len(message) < message_length:
                    chunk = client_socket.recv(message_length - len(message))
                    if not chunk:
                        break
                    message += chunk
                
                message_str = message.decode()
                print(f"Mensaje recibido de {client_address}: {message_str}")
                
                # Procesar mensaje
                if message_str.startswith('sinit'):
                    # Registro de servicio
                    service_name = message_str[5:]  # Obtener nombre del servicio
                    self.services[service_name] = client_socket
                    print(f"✓ Servicio '{service_name}' registrado desde {client_address}")
                    
                    # Enviar confirmación
                    response = "OK"
                    response_msg = f"{len(response):05d}{response}"
                    client_socket.send(response_msg.encode())
                    print(f"Confirmación enviada al servicio: {response_msg}")
                    
                elif 'Hello world' in message_str:
                    # Mensaje del cliente dirigido al servicio
                    service_name = 'servi'
                    if service_name in self.services:
                        service_socket = self.services[service_name]
                        # Guardar qué cliente envió el mensaje
                        self.client_service_map[service_socket] = client_socket
                        
                        # Reenviar mensaje al servicio
                        full_message = length_data + message
                        service_socket.send(full_message)
                        print(f"→ Mensaje del cliente reenviado al servicio '{service_name}'")
                    else:
                        print(f"✗ Servicio '{service_name}' no encontrado")
                        
                elif message_str.endswith('Received'):
                    # Respuesta del servicio, reenviar al cliente que lo solicitó
                    if client_socket in self.client_service_map:
                        original_client = self.client_service_map[client_socket]
                        full_message = length_data + message
                        original_client.send(full_message)
                        print(f"← Respuesta del servicio reenviada al cliente")
                        # Limpiar el mapeo
                        del self.client_service_map[client_socket]
                    else:
                        print("✗ No se encontró el cliente original para la respuesta")
                    
        except Exception as e:
            print(f"Error manejando cliente {client_address}: {e}")
        finally:
            # Limpiar conexiones
            for service_name, service_socket in list(self.services.items()):
                if service_socket == client_socket:
                    del self.services[service_name]
                    print(f"Servicio '{service_name}' desconectado")
                    
            client_socket.close()
            print(f"Conexión con {client_address} cerrada")

def main():
    bus = SOABus()
    
    # Crear socket del servidor
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind y listen
    server_address = ('localhost', 5000)
    server_socket.bind(server_address)
    server_socket.listen(5)
    
    print(f"Bus SOA escuchando en {server_address}")
    
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            bus.clients[client_address] = client_socket
            
            # Crear hilo para manejar cada cliente
            client_thread = threading.Thread(
                target=bus.handle_client,
                args=(client_socket, client_address)
            )
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        print("\nCerrando bus SOA...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()