"""
BaseDevice - Clase base abstracta para todos los módulos de dispositivos.
Cada dispositivo debe heredar de esta clase e implementar sus métodos.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from enum import Enum
import logging


class DeviceStatus(Enum):
    """Estados posibles de un dispositivo."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class BaseDevice(ABC):
    """
    Clase base para todos los módulos de dispositivos en PureVision.
    
    Cada módulo debe implementar los métodos abstractos:
    - initialize(): Configurar e inicializar el dispositivo
    - start(): Iniciar operación del dispositivo
    - stop(): Detener operación del dispositivo
    - process(): Procesar datos del dispositivo
    - cleanup(): Liberar recursos del dispositivo
    """
    
    def __init__(self, device_id: str, config: Dict[str, Any]):
        """
        Inicializa el dispositivo base.
        
        Args:
            device_id: Identificador único del dispositivo
            config: Diccionario de configuración del dispositivo
        """
        self.device_id = device_id
        self.config = config
        self.status = DeviceStatus.UNINITIALIZED
        self.logger = logging.getLogger(f"{self.__class__.__name__}[{device_id}]")
        self._callbacks = {}
        
    @abstractmethod
    def initialize(self) -> bool:
        """
        Inicializa el dispositivo y sus recursos.
        
        Returns:
            True si la inicialización fue exitosa, False en caso contrario
        """
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """
        Inicia la operación del dispositivo.
        
        Returns:
            True si el inicio fue exitoso, False en caso contrario
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """
        Detiene la operación del dispositivo.
        
        Returns:
            True si se detuvo correctamente, False en caso contrario
        """
        pass
    
    @abstractmethod
    def process(self, data: Optional[Any] = None) -> Any:
        """
        Procesa datos del dispositivo o ejecuta su lógica principal.
        
        Args:
            data: Datos de entrada opcionales
            
        Returns:
            Datos procesados o resultado de la operación
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """
        Libera todos los recursos del dispositivo.
        """
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """
        Retorna información del dispositivo.
        
        Returns:
            Diccionario con información del dispositivo
        """
        pass
    
    def set_status(self, status: DeviceStatus) -> None:
        """
        Actualiza el estado del dispositivo.
        
        Args:
            status: Nuevo estado del dispositivo
        """
        old_status = self.status
        self.status = status
        self.logger.info(f"Estado cambiado: {old_status.value} -> {status.value}")
        
        # Notificar cambio de estado
        self._trigger_callback("status_changed", {
            "old_status": old_status,
            "new_status": status
        })
    
    def get_status(self) -> DeviceStatus:
        """
        Obtiene el estado actual del dispositivo.
        
        Returns:
            Estado actual del dispositivo
        """
        return self.status
    
    def is_ready(self) -> bool:
        """
        Verifica si el dispositivo está listo para operar.
        
        Returns:
            True si está listo, False en caso contrario
        """
        return self.status in [DeviceStatus.READY, DeviceStatus.RUNNING]
    
    def register_callback(self, event: str, callback: callable) -> None:
        """
        Registra un callback para un evento específico.
        
        Args:
            event: Nombre del evento
            callback: Función a ejecutar cuando ocurra el evento
        """
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
        self.logger.debug(f"Callback registrado para evento: {event}")
    
    def _trigger_callback(self, event: str, data: Any = None) -> None:
        """
        Ejecuta los callbacks registrados para un evento.
        
        Args:
            event: Nombre del evento
            data: Datos a pasar al callback
        """
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(self, data)
                except Exception as e:
                    self.logger.error(f"Error en callback de {event}: {e}")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.device_id}, status={self.status.value})"
