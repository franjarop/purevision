#!/usr/bin/env python3
"""
add_custom_module.py - Ejemplo de cómo añadir un nuevo módulo de dispositivo.
"""

print("""
GUÍA: Cómo Añadir un Nuevo Módulo de Dispositivo
==================================================

1. COPIAR EL TEMPLATE
   -------------------
   Copiar el archivo template a src/modules/

   Windows:
   copy templates\\device_module_template.py src\\modules\\mi_modulo_module.py

   Linux/Mac:
   cp templates/device_module_template.py src/modules/mi_modulo_module.py


2. IMPLEMENTAR LA CLASE
   ---------------------
   Editar src/modules/mi_modulo_module.py:

   - Cambiar el nombre de la clase MiModuloModule
   - Implementar __init__() con parámetros de configuración
   - Implementar initialize() para configurar el dispositivo
   - Implementar start() para iniciar operaciones
   - Implementar stop() para detener operaciones
   - Implementar process() con la lógica principal
   - Implementar cleanup() para liberar recursos
   - Implementar get_info() para retornar información


3. CREAR CONFIGURACIÓN
   --------------------
   Crear config/mi_modulo_config.yaml:

   mi_modulo:
     parametro1: valor1
     parametro2: valor2


4. REGISTRAR EN devices.yaml
   --------------------------
   Añadir entrada en config/devices.yaml:

   devices:
     mi_dispositivo:
       module: "mi_modulo_module"
       enabled: true
       config:
         parametro1: valor1
         parametro2: valor2


5. PROBAR EL MÓDULO
   -----------------
   
   # Validar el módulo
   python module_manager.py validate mi_modulo_module

   # Listar módulos
   python module_manager.py list

   # Ver información
   python module_manager.py info mi_modulo_module

   # Ejecutar el sistema
   python main.py


EJEMPLO COMPLETO
================

Ver el archivo: templates/device_module_template.py

Para un ejemplo funcional, revisar:
- src/modules/camera_module.py
- src/modules/gpio_module.py
- src/modules/imu_module.py


ESTRUCTURA DEL MÓDULO
=====================

from src.core.base_device import BaseDevice, DeviceStatus

class MiModuloModule(BaseDevice):
    def __init__(self, device_id: str, config: Dict[str, Any]):
        super().__init__(device_id, config)
        # Tu inicialización
    
    def initialize(self) -> bool:
        # Configurar dispositivo
        return True
    
    def start(self) -> bool:
        # Iniciar operación
        return True
    
    def stop(self) -> bool:
        # Detener operación
        return True
    
    def process(self, data: Optional[Any] = None) -> Any:
        # Lógica principal
        return resultado
    
    def cleanup(self) -> None:
        # Liberar recursos
        pass
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "type": "mi_tipo",
            "status": self.status.value,
            # ... más información
        }


¿NECESITAS AYUDA?
=================

Consulta la documentación:
- docs/MODULE_DEVELOPMENT.md
- docs/API_REFERENCE.md

O revisa los ejemplos en:
- examples/
""")


if __name__ == "__main__":
    pass
