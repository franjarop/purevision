"""
DeviceManager - Gestor central de todos los dispositivos conectados.
Detecta, carga, administra y coordina todos los módulos de dispositivos.
"""

import logging
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
import importlib.util

from .base_device import BaseDevice, DeviceStatus
from .module_loader import ModuleLoader
from .event_bus import EventBus


class DeviceManager:
    """
    Gestor central de dispositivos del sistema PureVision.
    
    Responsabilidades:
    - Cargar y descargar módulos de dispositivos
    - Administrar el ciclo de vida de los dispositivos
    - Coordinar la comunicación entre dispositivos
    - Monitorear el estado de los dispositivos
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el gestor de dispositivos.
        
        Args:
            config: Configuración del sistema
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_bus = EventBus()
        self.module_loader = ModuleLoader(config.get("modules_path", "src/modules"))
        
        # Almacenamiento de dispositivos
        self.devices: Dict[str, BaseDevice] = {}
        self.device_types: Dict[str, Type[BaseDevice]] = {}
        
        self.logger.info("DeviceManager inicializado")
    
    def discover_modules(self) -> List[str]:
        """
        Descubre todos los módulos de dispositivos disponibles.
        
        Returns:
            Lista de nombres de módulos descubiertos
        """
        self.logger.info("Descubriendo módulos de dispositivos...")
        modules = self.module_loader.discover_modules()
        self.logger.info(f"Módulos descubiertos: {len(modules)}")
        return modules
    
    def load_module(self, module_name: str) -> bool:
        """
        Carga un módulo de dispositivo específico.
        
        Args:
            module_name: Nombre del módulo a cargar
            
        Returns:
            True si se cargó exitosamente, False en caso contrario
        """
        try:
            self.logger.info(f"Cargando módulo: {module_name}")
            device_class = self.module_loader.load_module(module_name)
            
            if device_class:
                self.device_types[module_name] = device_class
                self.logger.info(f"Módulo {module_name} cargado exitosamente")
                return True
            else:
                self.logger.error(f"No se pudo cargar el módulo {module_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al cargar módulo {module_name}: {e}")
            return False
    
    def create_device(self, module_name: str, device_id: str, 
                     config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Crea una instancia de un dispositivo.
        
        Args:
            module_name: Nombre del módulo del dispositivo
            device_id: Identificador único para el dispositivo
            config: Configuración específica del dispositivo
            
        Returns:
            ID del dispositivo creado o None si falló
        """
        try:
            # Verificar si el módulo está cargado
            if module_name not in self.device_types:
                if not self.load_module(module_name):
                    return None
            
            # Verificar si el ID ya existe
            if device_id in self.devices:
                self.logger.warning(f"Dispositivo {device_id} ya existe")
                return None
            
            # Crear instancia del dispositivo
            device_class = self.device_types[module_name]
            device_config = config or {}
            device = device_class(device_id, device_config)
            
            # Registrar callbacks del sistema
            device.register_callback("status_changed", self._on_device_status_changed)
            
            # Almacenar dispositivo
            self.devices[device_id] = device
            
            self.logger.info(f"Dispositivo {device_id} creado del módulo {module_name}")
            self.event_bus.publish("device_created", {
                "device_id": device_id,
                "module_name": module_name
            })
            
            return device_id
            
        except Exception as e:
            self.logger.error(f"Error al crear dispositivo {device_id}: {e}")
            return None
    
    def initialize_device(self, device_id: str) -> bool:
        """
        Inicializa un dispositivo específico.
        
        Args:
            device_id: ID del dispositivo a inicializar
            
        Returns:
            True si se inicializó correctamente, False en caso contrario
        """
        device = self.devices.get(device_id)
        if not device:
            self.logger.error(f"Dispositivo {device_id} no encontrado")
            return False
        
        try:
            self.logger.info(f"Inicializando dispositivo {device_id}...")
            device.set_status(DeviceStatus.INITIALIZING)
            
            if device.initialize():
                device.set_status(DeviceStatus.READY)
                self.logger.info(f"Dispositivo {device_id} inicializado correctamente")
                return True
            else:
                device.set_status(DeviceStatus.ERROR)
                self.logger.error(f"Fallo al inicializar dispositivo {device_id}")
                return False
                
        except Exception as e:
            device.set_status(DeviceStatus.ERROR)
            self.logger.error(f"Error al inicializar dispositivo {device_id}: {e}")
            return False
    
    def start_device(self, device_id: str) -> bool:
        """
        Inicia la operación de un dispositivo.
        
        Args:
            device_id: ID del dispositivo a iniciar
            
        Returns:
            True si se inició correctamente, False en caso contrario
        """
        device = self.devices.get(device_id)
        if not device:
            self.logger.error(f"Dispositivo {device_id} no encontrado")
            return False
        
        if not device.is_ready():
            self.logger.error(f"Dispositivo {device_id} no está listo (estado: {device.status.value})")
            return False
        
        try:
            if device.start():
                device.set_status(DeviceStatus.RUNNING)
                self.logger.info(f"Dispositivo {device_id} iniciado")
                return True
            else:
                self.logger.error(f"Fallo al iniciar dispositivo {device_id}")
                return False
                
        except Exception as e:
            device.set_status(DeviceStatus.ERROR)
            self.logger.error(f"Error al iniciar dispositivo {device_id}: {e}")
            return False
    
    def stop_device(self, device_id: str) -> bool:
        """
        Detiene la operación de un dispositivo.
        
        Args:
            device_id: ID del dispositivo a detener
            
        Returns:
            True si se detuvo correctamente, False en caso contrario
        """
        device = self.devices.get(device_id)
        if not device:
            self.logger.error(f"Dispositivo {device_id} no encontrado")
            return False
        
        try:
            if device.stop():
                device.set_status(DeviceStatus.READY)
                self.logger.info(f"Dispositivo {device_id} detenido")
                return True
            else:
                self.logger.error(f"Fallo al detener dispositivo {device_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al detener dispositivo {device_id}: {e}")
            return False
    
    def remove_device(self, device_id: str) -> bool:
        """
        Elimina un dispositivo del sistema.
        
        Args:
            device_id: ID del dispositivo a eliminar
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        device = self.devices.get(device_id)
        if not device:
            self.logger.error(f"Dispositivo {device_id} no encontrado")
            return False
        
        try:
            # Detener si está corriendo
            if device.status == DeviceStatus.RUNNING:
                self.stop_device(device_id)
            
            # Limpiar recursos
            device.cleanup()
            
            # Eliminar del diccionario
            del self.devices[device_id]
            
            self.logger.info(f"Dispositivo {device_id} eliminado")
            self.event_bus.publish("device_removed", {"device_id": device_id})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al eliminar dispositivo {device_id}: {e}")
            return False
    
    def get_device(self, device_id: str) -> Optional[BaseDevice]:
        """
        Obtiene una instancia de dispositivo.
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            Instancia del dispositivo o None si no existe
        """
        return self.devices.get(device_id)
    
    def list_devices(self) -> List[Dict[str, Any]]:
        """
        Lista todos los dispositivos registrados.
        
        Returns:
            Lista de información de dispositivos
        """
        return [
            {
                "id": device_id,
                "type": device.__class__.__name__,
                "status": device.status.value,
                "info": device.get_info()
            }
            for device_id, device in self.devices.items()
        ]
    
    def start_all(self) -> None:
        """Inicia todos los dispositivos listos."""
        self.logger.info("Iniciando todos los dispositivos...")
        for device_id, device in self.devices.items():
            if device.status == DeviceStatus.READY:
                self.start_device(device_id)
    
    def stop_all(self) -> None:
        """Detiene todos los dispositivos en ejecución."""
        self.logger.info("Deteniendo todos los dispositivos...")
        for device_id, device in self.devices.items():
            if device.status == DeviceStatus.RUNNING:
                self.stop_device(device_id)
    
    def cleanup_all(self) -> None:
        """Limpia todos los dispositivos."""
        self.logger.info("Limpiando todos los dispositivos...")
        device_ids = list(self.devices.keys())
        for device_id in device_ids:
            self.remove_device(device_id)
    
    def _on_device_status_changed(self, device: BaseDevice, data: Dict[str, Any]) -> None:
        """
        Callback para cambios de estado de dispositivos.
        
        Args:
            device: Dispositivo que cambió de estado
            data: Información del cambio
        """
        self.event_bus.publish("device_status_changed", {
            "device_id": device.device_id,
            "old_status": data["old_status"].value,
            "new_status": data["new_status"].value
        })
    
    def __del__(self):
        """Destructor para limpiar recursos."""
        self.cleanup_all()
