"""
Template para crear nuevos módulos de dispositivos.

Este template proporciona la estructura básica que debe seguir
cualquier módulo de dispositivo en PureVision.
"""

from typing import Any, Dict, Optional
import logging

import sys
sys.path.append('src')

from core.base_device import BaseDevice, DeviceStatus


class DeviceModuleTemplate(BaseDevice):
    """
    Template para módulos de dispositivos.
    
    Reemplaza esta clase con tu implementación específica.
    Ejemplo: class MiDispositivoModule(BaseDevice):
    
    Descripción del dispositivo y sus capacidades.
    """
    
    def __init__(self, device_id: str, config: Dict[str, Any]):
        """
        Inicializa el módulo del dispositivo.
        
        Args:
            device_id: Identificador único del dispositivo
            config: Configuración del dispositivo con parámetros específicos
        """
        super().__init__(device_id, config)
        
        # Extraer parámetros de configuración
        self.param1 = config.get("param1", "default_value")
        self.param2 = config.get("param2", 0)
        
        # Variables de estado del dispositivo
        self.device_handle = None
        self.is_connected = False
        
        # Estadísticas
        self.operation_count = 0
    
    def initialize(self) -> bool:
        """
        Inicializa el dispositivo y sus recursos.
        
        Aquí debes:
        - Abrir conexiones (puerto serial, I2C, etc.)
        - Configurar el dispositivo
        - Verificar que el dispositivo responde
        - Realizar calibración inicial si es necesario
        
        Returns:
            True si la inicialización fue exitosa, False en caso contrario
        """
        try:
            self.logger.info(f"Inicializando dispositivo...")
            
            # TODO: Implementar inicialización del dispositivo
            # Ejemplo:
            # self.device_handle = open_device_connection(self.param1)
            # self.device_handle.configure(self.param2)
            
            # Verificar conexión
            # if not self.device_handle.is_ready():
            #     self.logger.error("Dispositivo no responde")
            #     return False
            
            self.is_connected = True
            self.logger.info("Dispositivo inicializado correctamente")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al inicializar dispositivo: {e}")
            return False
    
    def start(self) -> bool:
        """
        Inicia la operación del dispositivo.
        
        Aquí debes:
        - Iniciar procesos de adquisición de datos
        - Activar sensores o actuadores
        - Comenzar loops de procesamiento
        
        Returns:
            True si el inicio fue exitoso, False en caso contrario
        """
        try:
            if not self.is_connected:
                self.logger.error("Dispositivo no está conectado")
                return False
            
            self.logger.info("Iniciando operación del dispositivo")
            
            # TODO: Implementar inicio del dispositivo
            # Ejemplo:
            # self.device_handle.start_acquisition()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al iniciar dispositivo: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Detiene la operación del dispositivo (sin desconectar).
        
        Aquí debes:
        - Pausar adquisición de datos
        - Desactivar sensores o actuadores
        - Detener loops de procesamiento
        
        Returns:
            True si se detuvo correctamente, False en caso contrario
        """
        try:
            self.logger.info("Deteniendo operación del dispositivo")
            
            # TODO: Implementar detención del dispositivo
            # Ejemplo:
            # self.device_handle.stop_acquisition()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al detener dispositivo: {e}")
            return False
    
    def process(self, data: Optional[Any] = None) -> Any:
        """
        Procesa datos del dispositivo o ejecuta su lógica principal.
        
        Este método se llama en el loop principal para:
        - Leer datos del dispositivo
        - Procesar información
        - Enviar comandos al dispositivo
        - Actualizar estado
        
        Args:
            data: Datos de entrada opcionales (depende del tipo de dispositivo)
            
        Returns:
            Datos procesados, resultado de la operación, o None si no hay datos
        """
        if not self.is_connected:
            self.logger.warning("Dispositivo no está conectado")
            return None
        
        try:
            # TODO: Implementar lógica de procesamiento
            # Ejemplo para un sensor:
            # sensor_data = self.device_handle.read()
            # processed_data = self.analyze(sensor_data)
            # self.operation_count += 1
            # return processed_data
            
            # Ejemplo para un actuador:
            # if data is not None:
            #     self.device_handle.write(data)
            #     self.operation_count += 1
            #     return {"success": True, "value": data}
            
            self.operation_count += 1
            return None
            
        except Exception as e:
            self.logger.error(f"Error en procesamiento: {e}")
            return None
    
    def cleanup(self) -> None:
        """
        Libera todos los recursos del dispositivo.
        
        Aquí debes:
        - Cerrar conexiones
        - Liberar memoria
        - Guardar estado si es necesario
        - Apagar dispositivo de forma segura
        """
        try:
            self.logger.info("Liberando recursos del dispositivo")
            
            # TODO: Implementar limpieza de recursos
            # Ejemplo:
            # if self.device_handle:
            #     self.device_handle.close()
            #     self.device_handle = None
            
            self.is_connected = False
            self.logger.info("Recursos liberados correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al liberar recursos: {e}")
    
    def get_info(self) -> Dict[str, Any]:
        """
        Retorna información del dispositivo.
        
        Proporciona información útil sobre:
        - Tipo de dispositivo
        - Estado actual
        - Configuración
        - Estadísticas de operación
        - Cualquier información relevante
        
        Returns:
            Diccionario con información del dispositivo
        """
        return {
            "type": "template_device",  # Cambiar por el tipo real
            "device_id": self.device_id,
            "status": self.status.value,
            "is_connected": self.is_connected,
            "config": {
                "param1": self.param1,
                "param2": self.param2
            },
            "statistics": {
                "operation_count": self.operation_count
            }
        }
    
    # Métodos adicionales específicos del dispositivo
    # ------------------------------------------------
    
    def custom_method(self, param: Any) -> Any:
        """
        Métodos personalizados para funcionalidad específica.
        
        Puedes añadir todos los métodos que necesites para
        la funcionalidad específica de tu dispositivo.
        """
        pass


# Ejemplo de uso (no ejecutar en producción)
if __name__ == "__main__":
    # Configuración de ejemplo
    config = {
        "param1": "valor1",
        "param2": 42
    }
    
    # Crear instancia
    device = DeviceModuleTemplate("test_device", config)
    
    # Usar el dispositivo
    if device.initialize():
        device.start()
        result = device.process()
        print(f"Resultado: {result}")
        print(f"Info: {device.get_info()}")
        device.stop()
        device.cleanup()
