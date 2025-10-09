"""
Service Logger - Utilidades de logging para servicios SOA
==========================================================
Modulo reutilizable para logging consistente y colorido en todos los servicios.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from colorama import Fore, Style, init
import time

# Inicializar colorama para colores en Windows
init(autoreset=True)


class ServiceLogger:
    """Logger para servicios SOA con formato consistente y colores"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name.upper()
        self.start_time = None
        
    def _format_timestamp(self) -> str:
        """Genera timestamp formateado"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def _print_log(self, icon: str, color: str, event: str, message: str, details: Dict = None):
        """Imprime un log formateado"""
        timestamp = self._format_timestamp()
        log_line = f"{Fore.WHITE}[{timestamp}] {color}[{self.service_name}] {icon} {event}{Style.RESET_ALL} -> {message}"
        print(log_line)
        
        # Imprimir detalles con indentacion
        if details:
            for key, value in details.items():
                print(f"{Fore.WHITE}  |-- {Fore.CYAN}{key}{Style.RESET_ALL}: {value}")
    
    def startup(self, url: str):
        """Log de inicio del servicio"""
        self._print_log(
            "[START]",
            Fore.MAGENTA,
            "STARTUP",
            f"Servicio iniciando...",
            details={"URL": url}
        )
    
    def registered(self, bus_url: str):
        """Log de registro exitoso en el bus"""
        self._print_log(
            "[OK]",
            Fore.GREEN,
            "REGISTERED",
            f"Registrado en el Bus SOA",
            details={"Bus URL": bus_url}
        )
    
    def request_received(self, method: str, endpoint: str, params: Dict = None):
        """Log de request recibido"""
        self.start_time = time.time()
        
        details = {
            "Metodo": method,
            "Endpoint": endpoint,
            "Timestamp": self._format_timestamp()
        }
        
        if params:
            # Limitar longitud del payload mostrado
            params_str = str(params)
            if len(params_str) > 100:
                params_str = params_str[:100] + "..."
            details["Parametros"] = params_str
        
        self._print_log(
            "[<<]",
            Fore.CYAN,
            "REQUEST",
            f"Request recibido",
            details=details
        )
    
    def db_query(self, query: str, params: Dict = None):
        """Log de consulta a base de datos"""
        # Limpiar y formatear query
        query_clean = " ".join(query.split())
        if len(query_clean) > 150:
            query_clean = query_clean[:150] + "..."
        
        details = {"Query": query_clean}
        if params:
            details["Params"] = str(params)
        
        self._print_log(
            "[DB]",
            Fore.YELLOW,
            "DB QUERY",
            f"Ejecutando consulta SQL",
            details=details
        )
    
    def response_sent(self, status_code: int, message: str = None, data_summary: str = None):
        """Log de respuesta enviada"""
        elapsed_ms = 0
        if self.start_time:
            elapsed_ms = round((time.time() - self.start_time) * 1000, 2)
            self.start_time = None
        
        # Color segun status code
        if status_code < 300:
            icon, color = "[OK]", Fore.GREEN
            result = "SUCCESS"
        elif status_code < 400:
            icon, color = "[>>]", Fore.CYAN
            result = "REDIRECT"
        elif status_code < 500:
            icon, color = "[WARN]", Fore.YELLOW
            result = "CLIENT ERROR"
        else:
            icon, color = "[ERROR]", Fore.RED
            result = "SERVER ERROR"
        
        details = {
            "Status Code": status_code,
            "Resultado": result,
            "Tiempo procesamiento": f"{elapsed_ms}ms"
        }
        
        if message:
            details["Mensaje"] = message
        
        if data_summary:
            details["Datos"] = data_summary
        
        self._print_log(
            icon,
            color,
            "RESPONSE",
            f"Respuesta enviada",
            details=details
        )
    
    def error(self, error_type: str, error_message: str, details: Dict = None):
        """Log de error"""
        self._print_log(
            "[ERROR]",
            Fore.RED,
            "ERROR",
            f"{error_type}",
            details={"Error": error_message, **(details or {})}
        )
    
    def warning(self, message: str, details: Dict = None):
        """Log de advertencia"""
        self._print_log(
            "[WARN]",
            Fore.YELLOW,
            "WARNING",
            message,
            details=details
        )
    
    def info(self, message: str, details: Dict = None):
        """Log de informacion general"""
        self._print_log(
            "[INFO]",
            Fore.BLUE,
            "INFO",
            message,
            details=details
        )


# Funcion auxiliar para crear loggers
def create_service_logger(service_name: str) -> ServiceLogger:
    """
    Crea un logger para un servicio especifico.
    
    Uso:
        logger = create_service_logger("regist")
        logger.startup("http://regist:8000")
    """
    return ServiceLogger(service_name)
