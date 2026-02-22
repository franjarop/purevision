# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-21

### Añadido
- Arquitectura modular completa para dispositivos
- Sistema core con DeviceManager, ModuleLoader, EventBus y ConfigManager
- Módulo de cámara (CSI y USB) para Jetson Nano
- Módulo de magnificación euleriana con múltiples presets
- Módulo de GPIO para control de pines
- Módulo de display para visualización
- Módulo IMU de ejemplo
- Handlers específicos para cámaras CSI y USB
- Sistema de procesamiento con pipeline configurable
- Filtros de imagen y video
- Utilidades: Visualizer, FPSCounter, Logger, DeviceDetector
- Configuraciones YAML para todos los módulos
- Scripts principales: main.py, device_list.py, module_manager.py
- Ejemplos de uso y templates para nuevos módulos
- Documentación completa del proyecto

### Características Principales
- Plug & Play: Detección automática de dispositivos
- Modular: Cada dispositivo tiene su propio módulo
- Extensible: Fácil añadir nuevos dispositivos
- Configurable: Todo configurable vía YAML
- Optimizado para Jetson Nano Orin

[0.1.0]: https://github.com/yourusername/purevision/releases/tag/v0.1.0
