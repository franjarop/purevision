"""
ModuleLoader - Cargador dinámico de módulos de dispositivos.
Descubre y carga módulos de dispositivos en tiempo de ejecución.
"""

import logging
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Type
import sys

from .base_device import BaseDevice


class ModuleLoader:
    """
    Cargador dinámico de módulos de dispositivos.
    
    Permite cargar módulos de dispositivos en tiempo de ejecución,
    facilitando la extensibilidad del sistema sin necesidad de recompilar.
    """
    
    def __init__(self, modules_path: str):
        """
        Inicializa el cargador de módulos.
        
        Args:
            modules_path: Ruta al directorio de módulos
        """
        self.modules_path = Path(modules_path)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.loaded_modules: Dict[str, Type[BaseDevice]] = {}
        
        self.logger.info(f"ModuleLoader inicializado (path: {self.modules_path})")
    
    def discover_modules(self) -> List[str]:
        """
        Descubre todos los módulos de dispositivos disponibles.
        
        Returns:
            Lista de nombres de módulos encontrados
        """
        modules = []
        
        if not self.modules_path.exists():
            self.logger.warning(f"Directorio de módulos no existe: {self.modules_path}")
            return modules
        
        # Buscar archivos Python en el directorio de módulos
        for file_path in self.modules_path.glob("*_module.py"):
            if file_path.stem != "__init__":
                modules.append(file_path.stem)
        
        self.logger.info(f"Módulos descubiertos: {modules}")
        return modules
    
    def load_module(self, module_name: str) -> Optional[Type[BaseDevice]]:
        """
        Carga un módulo de dispositivo específico.
        
        Args:
            module_name: Nombre del módulo a cargar (sin extensión .py)
            
        Returns:
            Clase del dispositivo o None si no se pudo cargar
        """
        # Verificar si ya está cargado
        if module_name in self.loaded_modules:
            self.logger.info(f"Módulo {module_name} ya está cargado")
            return self.loaded_modules[module_name]
        
        try:
            # Construir la ruta completa al módulo
            module_file = self.modules_path / f"{module_name}.py"
            
            if not module_file.exists():
                self.logger.error(f"Archivo de módulo no encontrado: {module_file}")
                return None
            
            # Cargar el módulo dinámicamente
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            if spec is None or spec.loader is None:
                self.logger.error(f"No se pudo crear spec para {module_name}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Buscar la clase del dispositivo en el módulo
            device_class = self._find_device_class(module)
            
            if device_class:
                self.loaded_modules[module_name] = device_class
                self.logger.info(f"Módulo {module_name} cargado: {device_class.__name__}")
                return device_class
            else:
                self.logger.error(f"No se encontró clase de dispositivo en {module_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error al cargar módulo {module_name}: {e}", exc_info=True)
            return None
    
    def _find_device_class(self, module) -> Optional[Type[BaseDevice]]:
        """
        Busca una clase que herede de BaseDevice en el módulo.
        
        Args:
            module: Módulo cargado
            
        Returns:
            Clase del dispositivo o None si no se encuentra
        """
        for item_name in dir(module):
            item = getattr(module, item_name)
            
            # Verificar si es una clase
            if not isinstance(item, type):
                continue
            
            # Verificar si hereda de BaseDevice (pero no es BaseDevice misma)
            if issubclass(item, BaseDevice) and item is not BaseDevice:
                return item
        
        return None
    
    def unload_module(self, module_name: str) -> bool:
        """
        Descarga un módulo previamente cargado.
        
        Args:
            module_name: Nombre del módulo a descargar
            
        Returns:
            True si se descargó exitosamente, False en caso contrario
        """
        if module_name in self.loaded_modules:
            del self.loaded_modules[module_name]
            
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            self.logger.info(f"Módulo {module_name} descargado")
            return True
        else:
            self.logger.warning(f"Módulo {module_name} no está cargado")
            return False
    
    def reload_module(self, module_name: str) -> Optional[Type[BaseDevice]]:
        """
        Recarga un módulo (útil durante desarrollo).
        
        Args:
            module_name: Nombre del módulo a recargar
            
        Returns:
            Clase del dispositivo recargada o None si falló
        """
        self.logger.info(f"Recargando módulo {module_name}")
        self.unload_module(module_name)
        return self.load_module(module_name)
    
    def get_loaded_modules(self) -> List[str]:
        """
        Obtiene la lista de módulos cargados actualmente.
        
        Returns:
            Lista de nombres de módulos cargados
        """
        return list(self.loaded_modules.keys())
    
    def validate_module(self, module_name: str) -> bool:
        """
        Valida que un módulo tenga la estructura correcta.
        
        Args:
            module_name: Nombre del módulo a validar
            
        Returns:
            True si el módulo es válido, False en caso contrario
        """
        module_file = self.modules_path / f"{module_name}.py"
        
        if not module_file.exists():
            self.logger.error(f"Archivo no encontrado: {module_file}")
            return False
        
        try:
            # Intentar cargar el módulo
            device_class = self.load_module(module_name)
            
            if not device_class:
                return False
            
            # Verificar que tenga los métodos requeridos
            required_methods = ["initialize", "start", "stop", "process", "cleanup", "get_info"]
            for method in required_methods:
                if not hasattr(device_class, method):
                    self.logger.error(f"Módulo {module_name} no tiene el método {method}")
                    return False
            
            self.logger.info(f"Módulo {module_name} es válido")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al validar módulo {module_name}: {e}")
            return False
