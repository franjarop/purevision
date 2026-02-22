"""
ConfigManager - Gestor centralizado de configuraciones del sistema.
Carga y gestiona configuraciones desde archivos YAML.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class ConfigManager:
    """
    Gestor de configuraciones del sistema PureVision.
    
    Carga configuraciones desde archivos YAML y las hace disponibles
    para todos los componentes del sistema.
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Inicializa el gestor de configuraciones.
        
        Args:
            config_dir: Directorio donde se encuentran los archivos de configuración
        """
        self.config_dir = Path(config_dir)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.configs: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info(f"ConfigManager inicializado (dir: {self.config_dir})")
    
    def load_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Carga un archivo de configuración.
        
        Args:
            config_name: Nombre del archivo de configuración (sin extensión)
            
        Returns:
            Diccionario con la configuración o None si no se pudo cargar
        """
        config_file = self.config_dir / f"{config_name}.yaml"
        
        if not config_file.exists():
            self.logger.error(f"Archivo de configuración no encontrado: {config_file}")
            return None
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.configs[config_name] = config
            self.logger.info(f"Configuración '{config_name}' cargada exitosamente")
            return config
            
        except Exception as e:
            self.logger.error(f"Error al cargar configuración '{config_name}': {e}")
            return None
    
    def get_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene una configuración previamente cargada.
        
        Args:
            config_name: Nombre de la configuración
            
        Returns:
            Diccionario con la configuración o None si no existe
        """
        if config_name not in self.configs:
            return self.load_config(config_name)
        
        return self.configs.get(config_name)
    
    def get_value(self, config_name: str, key_path: str, default: Any = None) -> Any:
        """
        Obtiene un valor específico de una configuración usando notación de punto.
        
        Args:
            config_name: Nombre de la configuración
            key_path: Ruta al valor (ej: "camera.resolution.width")
            default: Valor por defecto si no se encuentra
            
        Returns:
            Valor encontrado o el valor por defecto
        """
        config = self.get_config(config_name)
        
        if not config:
            return default
        
        # Navegar por la estructura usando la ruta de claves
        keys = key_path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set_value(self, config_name: str, key_path: str, value: Any) -> bool:
        """
        Establece un valor en una configuración usando notación de punto.
        
        Args:
            config_name: Nombre de la configuración
            key_path: Ruta al valor (ej: "camera.resolution.width")
            value: Nuevo valor a establecer
            
        Returns:
            True si se estableció correctamente, False en caso contrario
        """
        config = self.get_config(config_name)
        
        if not config:
            self.logger.error(f"Configuración '{config_name}' no encontrada")
            return False
        
        # Navegar y crear la estructura si es necesario
        keys = key_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Establecer el valor final
        current[keys[-1]] = value
        self.logger.debug(f"Valor establecido: {config_name}.{key_path} = {value}")
        
        return True
    
    def save_config(self, config_name: str) -> bool:
        """
        Guarda una configuración modificada de vuelta a su archivo.
        
        Args:
            config_name: Nombre de la configuración a guardar
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        if config_name not in self.configs:
            self.logger.error(f"Configuración '{config_name}' no está cargada")
            return False
        
        config_file = self.config_dir / f"{config_name}.yaml"
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.configs[config_name], f, default_flow_style=False)
            
            self.logger.info(f"Configuración '{config_name}' guardada en {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al guardar configuración '{config_name}': {e}")
            return False
    
    def reload_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Recarga una configuración desde el archivo.
        
        Args:
            config_name: Nombre de la configuración a recargar
            
        Returns:
            Configuración recargada o None si falló
        """
        if config_name in self.configs:
            del self.configs[config_name]
        
        return self.load_config(config_name)
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene todas las configuraciones cargadas.
        
        Returns:
            Diccionario con todas las configuraciones
        """
        return self.configs.copy()
    
    def list_available_configs(self) -> list[str]:
        """
        Lista todos los archivos de configuración disponibles.
        
        Returns:
            Lista de nombres de configuraciones disponibles
        """
        if not self.config_dir.exists():
            self.logger.warning(f"Directorio de configuración no existe: {self.config_dir}")
            return []
        
        config_files = []
        for file_path in self.config_dir.glob("*.yaml"):
            config_files.append(file_path.stem)
        
        return sorted(config_files)
