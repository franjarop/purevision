# Arquitectura del Sistema - PureVision

## Visión General

PureVision es un sistema modular de procesamiento de video diseñado específicamente para NVIDIA Jetson Nano Orin. La arquitectura está basada en el principio **"dispositivo → módulo"**, donde cada dispositivo conectado tiene su propio módulo independiente.

## Principios de Diseño

### 1. Modularidad
Cada dispositivo es un módulo auto-contenido que hereda de `BaseDevice`.

### 2. Extensibilidad
Nuevos dispositivos pueden añadirse sin modificar el core del sistema.

### 3. Configurabilidad
Todo el sistema se configura mediante archivos YAML.

### 4. Desacoplamiento
Los módulos se comunican a través del EventBus, no directamente.

## Estructura del Proyecto

```
purevision/
├── src/
│   ├── core/              # Núcleo del sistema
│   │   ├── base_device.py        # Clase base para dispositivos
│   │   ├── device_manager.py     # Gestión de dispositivos
│   │   ├── module_loader.py      # Carga dinámica de módulos
│   │   ├── event_bus.py          # Sistema de eventos
│   │   └── config_manager.py     # Gestión de configuración
│   │
│   ├── modules/           # Módulos de dispositivos
│   │   ├── camera_module.py
│   │   ├── eulerian_processor_module.py
│   │   ├── gpio_module.py
│   │   ├── display_module.py
│   │   └── imu_module.py
│   │
│   ├── devices/           # Handlers específicos
│   │   ├── camera_csi_handler.py
│   │   ├── camera_usb_handler.py
│   │   └── camera_factory.py
│   │
│   └── processing/        # Algoritmos
│       ├── eulerian_magnification.py
│       ├── video_pipeline.py
│       └── filters.py
│
├── config/                # Configuraciones
│   ├── system.yaml
│   ├── devices.yaml
│   ├── camera_module.yaml
│   └── eulerian_module.yaml
│
├── utils/                 # Utilidades
│   ├── visualizer.py
│   ├── fps_counter.py
│   ├── logger.py
│   └── device_detector.py
│
├── examples/              # Ejemplos
├── templates/             # Templates para nuevos módulos
└── docs/                  # Documentación
```

## Componentes Principales

### Core

#### BaseDevice
```python
class BaseDevice(ABC):
    """Clase base abstracta para todos los dispositivos."""
    
    @abstractmethod
    def initialize(self) -> bool: pass
    
    @abstractmethod
    def start(self) -> bool: pass
    
    @abstractmethod
    def stop(self) -> bool: pass
    
    @abstractmethod
    def process(self, data) -> Any: pass
    
    @abstractmethod
    def cleanup(self) -> None: pass
    
    @abstractmethod
    def get_info(self) -> Dict: pass
```

**Responsabilidades:**
- Definir interfaz común para todos los dispositivos
- Gestionar estados del dispositivo
- Proporcionar sistema de callbacks
- Logging unificado

#### DeviceManager
```python
class DeviceManager:
    """Gestor central de todos los dispositivos."""
```

**Responsabilidades:**
- Descubrir módulos disponibles
- Cargar y descargar módulos dinámicamente
- Crear instancias de dispositivos
- Administrar ciclo de vida de dispositivos
- Coordinar comunicación entre dispositivos

#### ModuleLoader
```python
class ModuleLoader:
    """Cargador dinámico de módulos."""
```

**Responsabilidades:**
- Descubrir archivos de módulos
- Cargar módulos en tiempo de ejecución
- Validar estructura de módulos
- Cachear módulos cargados
- Permitir recarga en caliente

#### EventBus
```python
class EventBus:
    """Sistema de eventos pub-sub."""
```

**Responsabilidades:**
- Publicar eventos del sistema
- Gestionar suscripciones
- Despachar eventos asíncronamente
- Desacoplar comunicación entre módulos

#### ConfigManager
```python
class ConfigManager:
    """Gestor de configuraciones YAML."""
```

**Responsabilidades:**
- Cargar archivos de configuración
- Proporcionar acceso a valores
- Guardar configuraciones modificadas
- Validar configuraciones

### Módulos de Dispositivos

Cada módulo sigue este patrón:

```python
class XxxModule(BaseDevice):
    def __init__(self, device_id: str, config: Dict):
        super().__init__(device_id, config)
        # Inicialización específica
    
    def initialize(self) -> bool:
        # Configurar dispositivo
        return True
    
    def start(self) -> bool:
        # Iniciar operación
        return True
    
    def stop(self) -> bool:
        # Detener operación
        return True
    
    def process(self, data=None) -> Any:
        # Lógica principal
        return result
    
    def cleanup(self) -> None:
        # Liberar recursos
        pass
    
    def get_info(self) -> Dict:
        return {"type": "xxx", ...}
```

## Flujo de Datos

```
┌─────────────┐
│   Camera    │
│   Module    │
└──────┬──────┘
       │ frame
       v
┌─────────────┐
│  Eulerian   │
│  Processor  │
│   Module    │
└──────┬──────┘
       │ processed frame
       v
┌─────────────┐
│   Display   │
│   Module    │
└─────────────┘
```

## Ciclo de Vida de un Dispositivo

```
UNINITIALIZED
     │
     │ initialize()
     v
INITIALIZING
     │
     │ success
     v
   READY
     │
     │ start()
     v
  RUNNING ←──────┐
     │           │
     │ stop()    │ resume()
     v           │
  PAUSED ────────┘
     │
     │ cleanup()
     v
DISCONNECTED
```

## Estados del Sistema

```python
class DeviceStatus(Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    DISCONNECTED = "disconnected"
```

## Sistema de Eventos

### Eventos del Sistema

| Evento | Datos | Descripción |
|--------|-------|-------------|
| `device_created` | device_id, module_name | Dispositivo creado |
| `device_removed` | device_id | Dispositivo eliminado |
| `device_status_changed` | device_id, old_status, new_status | Cambio de estado |
| `frame_captured` | device_id, frame, timestamp | Frame capturado |
| `processing_complete` | device_id, result | Procesamiento completo |
| `error_occurred` | device_id, error_msg | Error en dispositivo |

### Uso del EventBus

```python
# Publicar evento
event_bus.publish("device_status_changed", {
    "device_id": "camera_0",
    "old_status": "ready",
    "new_status": "running"
})

# Suscribirse a evento
def on_status_changed(data):
    print(f"Device {data['device_id']} changed to {data['new_status']}")

event_bus.subscribe("device_status_changed", on_status_changed)
```

## Pipeline de Procesamiento

```python
pipeline = VideoPipeline("main_pipeline")

# Añadir etapas
pipeline.add_stage("capture", camera.process)
pipeline.add_stage("denoise", filters.denoise)
pipeline.add_stage("magnify", processor.process)
pipeline.add_stage("display", display.process)

# Procesar frame
result = pipeline.process_frame(input_frame)
```

## Configuración en Cascada

```
system.yaml (global)
    ↓
devices.yaml (dispositivos)
    ↓
camera_module.yaml (módulo específico)
    ↓
runtime overrides (argumentos CLI)
```

## Patrones de Diseño Utilizados

### 1. Abstract Factory
`BaseDevice` define la interfaz para crear dispositivos.

### 2. Observer
`EventBus` implementa el patrón observador.

### 3. Strategy
Diferentes estrategias de procesamiento (presets eulerianos).

### 4. Singleton
`ConfigManager` y `EventBus` son singletons.

### 5. Template Method
`BaseDevice` define el template para todos los dispositivos.

### 6. Factory Method
`CameraFactory` crea instancias específicas de cámaras.

## Extensibilidad

### Añadir Nuevo Módulo

1. **Copiar template**
   ```bash
   cp templates/device_module_template.py src/modules/mi_modulo_module.py
   ```

2. **Implementar clase**
   ```python
   class MiModuloModule(BaseDevice):
       # Implementar métodos abstractos
   ```

3. **Crear configuración**
   ```yaml
   # config/mi_modulo_config.yaml
   mi_modulo:
     param1: valor1
   ```

4. **Registrar en devices.yaml**
   ```yaml
   devices:
     mi_dispositivo:
       module: "mi_modulo_module"
       enabled: true
   ```

5. **Usar**
   ```python
   device_manager.create_device("mi_modulo_module", "mi_id", config)
   ```

## Consideraciones de Rendimiento

### Optimizaciones GPU
- OpenCV con soporte CUDA
- nvvidconv para conversión de video
- nvarguscamerasrc para cámaras CSI

### Threading
- EventBus con dispatch asíncrono
- Pipeline con etapas paralelas opcionales
- Procesamiento en threads separados

### Memoria
- Buffers circulares limitados
- Liberación explícita de recursos
- Reutilización de arrays NumPy

## Seguridad

- Validación de módulos antes de cargar
- Manejo de errores robusto
- Cleanup automático de recursos
- Timeouts en operaciones de I/O
- Logging de todas las operaciones

## Testing

```python
# test_camera_module.py
def test_camera_initialize():
    camera = CameraModule("test", config)
    assert camera.initialize() == True
    assert camera.status == DeviceStatus.READY
```

## Debugging

```python
# Activar logging detallado
logger = setup_logger("PureVision", level=logging.DEBUG)

# Usar context manager para cambiar nivel temporalmente
with LoggerContext(logger, logging.DEBUG):
    device_manager.create_device(...)
```

## Monitoreo

```python
# Obtener estadísticas
stats = device_manager.get_device("camera_0").get_info()
print(f"Frames capturados: {stats['frames_captured']}")

# Pipeline stats
pipeline_stats = pipeline.get_stats()
print(f"FPS promedio: {pipeline_stats['average_fps']}")
```
