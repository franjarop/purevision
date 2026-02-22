# PureVision

Sistema modular de procesamiento de video con magnificación euleriana para Jetson Nano Orin.

## 🎯 Características Principales

- **Arquitectura Modular**: Cada dispositivo conectado tiene su propio módulo independiente
- **Plug & Play**: Detección automática de dispositivos conectados
- **Magnificación Euleriana**: Amplificación de movimientos y variaciones de color imperceptibles
- **Optimizado para Jetson**: Aprovecha las capacidades de GPU de Jetson Nano Orin
- **Extensible**: Fácil de añadir nuevos módulos para diferentes dispositivos

## 🏗️ Arquitectura

```
purevision/
├── src/
│   ├── core/              # Core del sistema (gestión modular)
│   ├── modules/           # Módulos de dispositivos
│   ├── devices/           # Handlers específicos de dispositivos
│   └── processing/        # Algoritmos de procesamiento
├── config/                # Configuraciones YAML
├── examples/              # Ejemplos de uso
├── docs/                  # Documentación
├── templates/             # Templates para nuevos módulos
└── utils/                 # Utilidades del sistema
```

## 📋 Requisitos

### Hardware
- NVIDIA Jetson Nano Orin (6GB o 8GB)
- Cámara CSI o USB compatible
- Tarjeta SD con al menos 32GB
- Fuente de alimentación adecuada (5V 4A recomendado)

### Software
- JetPack 5.0 o superior
- Python 3.8+
- CUDA 11.4+
- OpenCV con soporte CUDA

## 🚀 Instalación

### 1. Preparar el entorno en Jetson Nano Orin

```bash
# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y python3-pip python3-dev
sudo apt install -y libhdf5-serial-dev hdf5-tools libhdf5-dev
sudo apt install -y libatlas-base-dev gfortran
```

### 2. Clonar el repositorio

```bash
cd ~/Documents/Proyectos
git clone https://github.com/yourusername/purevision.git
cd purevision
```

### 3. Instalar dependencias de Python

```bash
# Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate

# Instalar paquetes
pip install -r requirements.txt

# Instalación en modo desarrollo
pip install -e .
```

## 📖 Uso Rápido

### Listar dispositivos detectados

```bash
python device_list.py
```

### Ejecutar demo en tiempo real

```bash
python examples/eulerian_realtime.py
```

### Ejecutar sistema principal

```bash
python main.py --config config/system.yaml
```

## 🔧 Módulos Disponibles

| Módulo | Descripción | Estado |
|--------|-------------|--------|
| `camera_module` | Cámaras CSI/USB | ✅ Activo |
| `eulerian_processor_module` | Magnificación euleriana | ✅ Activo |
| `gpio_module` | Control GPIO | ✅ Activo |
| `display_module` | Salida de video | ✅ Activo |
| `imu_module` | Sensores IMU | 🔄 Ejemplo |

## 📚 Documentación

- [Guía de Instalación](docs/INSTALLATION.md)
- [Arquitectura del Sistema](docs/ARCHITECTURE.md)
- [Desarrollo de Módulos](docs/MODULE_DEVELOPMENT.md)
- [Dispositivos Soportados](docs/DEVICE_SUPPORT.md)
- [Referencia de API](docs/API_REFERENCE.md)

## 🎓 Magnificación Euleriana

La magnificación euleriana es una técnica de procesamiento de video que amplifica variaciones temporales sutiles en videos. Esto permite visualizar:

- Cambios de color relacionados con el flujo sanguíneo
- Movimientos imperceptibles
- Vibraciones estructurales
- Respiración y pulso cardíaco

### Aplicaciones

- 🏥 Monitoreo de signos vitales sin contacto
- 🔬 Análisis de vibraciones en estructuras
- 🎥 Efectos visuales y arte digital
- 🔧 Inspección industrial

## 🛠️ Añadir un Nuevo Módulo

1. Copiar el template:
```bash
cp templates/device_module_template.py src/modules/my_new_module.py
```

2. Implementar la clase del dispositivo:
```python
from src.core.base_device import BaseDevice

class MyNewDevice(BaseDevice):
    def initialize(self):
        # Tu código de inicialización
        pass
    
    def process(self, data):
        # Tu lógica de procesamiento
        return processed_data
```

3. Registrar en `config/devices.yaml`

Consulta [MODULE_DEVELOPMENT.md](docs/MODULE_DEVELOPMENT.md) para más detalles.

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 👨‍💻 Autor

**Javier Robles**

## 🙏 Agradecimientos

- MIT Media Lab por el algoritmo de magnificación euleriana
- NVIDIA por la plataforma Jetson
- La comunidad open source

## 📞 Soporte

Si tienes problemas o preguntas:
- Abre un [issue](https://github.com/yourusername/purevision/issues)
- Consulta la [documentación](docs/)
- Revisa los [ejemplos](examples/)
