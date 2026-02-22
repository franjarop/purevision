# Guía de Instalación - PureVision

## Requisitos del Sistema

### Hardware Requerido
- **NVIDIA Jetson Nano Orin** (6GB o 8GB recomendado)
- **Tarjeta SD/eMMC**: Mínimo 32GB (64GB recomendado)
- **Fuente de alimentación**: 5V 4A con barrel jack
- **Cámara**: CSI (Raspberry Pi Camera) o USB compatible
- **(Opcional)** Disipador de calor y ventilador

### Software Requerido
- **JetPack 5.0** o superior
- **Python 3.8+**
- **CUDA 11.4+**
- **OpenCV** con soporte CUDA

## Instalación Paso a Paso

### 1. Preparar Jetson Nano Orin

#### Flashear JetPack
```bash
# Descargar SDK Manager desde:
# https://developer.nvidia.com/nvidia-sdk-manager

# O usar comando directo (en host Ubuntu):
sudo apt install nvidia-jetpack
```

#### Configuración Inicial
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y \
    python3-pip \
    python3-dev \
    python3-numpy \
    libhdf5-serial-dev \
    hdf5-tools \
    libhdf5-dev \
    libatlas-base-dev \
    gfortran \
    git \
    cmake
```

### 2. Configurar OpenCV con CUDA

#### Verificar OpenCV existente
```bash
python3 -c "import cv2; print(cv2.__version__); print(cv2.cuda.getCudaEnabledDeviceCount())"
```

#### Compilar OpenCV con CUDA (si es necesario)
```bash
# Clonar OpenCV
cd ~
git clone https://github.com/opencv/opencv.git
git clone https://github.com/opencv/opencv_contrib.git
cd opencv
git checkout 4.8.0
cd ../opencv_contrib
git checkout 4.8.0

# Compilar
cd ../opencv
mkdir build && cd build

cmake -D CMAKE_BUILD_TYPE=RELEASE \
      -D CMAKE_INSTALL_PREFIX=/usr/local \
      -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
      -D WITH_CUDA=ON \
      -D CUDA_ARCH_BIN="8.7" \
      -D CUDA_ARCH_PTX="" \
      -D WITH_CUDNN=ON \
      -D OPENCV_DNN_CUDA=ON \
      -D ENABLE_FAST_MATH=ON \
      -D CUDA_FAST_MATH=ON \
      -D WITH_CUBLAS=ON \
      -D WITH_GSTREAMER=ON \
      -D WITH_LIBV4L=ON \
      -D BUILD_opencv_python3=ON \
      -D BUILD_TESTS=OFF \
      -D BUILD_PERF_TESTS=OFF \
      -D BUILD_EXAMPLES=OFF \
      ..

make -j4
sudo make install
sudo ldconfig
```

### 3. Instalar PureVision

#### Clonar Repositorio
```bash
cd ~/Documents/Proyectos
git clone https://github.com/yourusername/purevision.git
cd purevision
```

#### Crear Entorno Virtual
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Instalar Dependencias
```bash
# Actualizar pip
pip install --upgrade pip

# Instalar paquetes
pip install -r requirements.txt

# Instalación en modo desarrollo
pip install -e .
```

#### Configurar Jetson.GPIO
```bash
# Añadir usuario al grupo gpio
sudo usermod -a -G gpio $USER

# Configurar permisos
sudo groupadd -f -r gpio
sudo usermod -a -G gpio $USER

# Reiniciar para aplicar cambios
sudo reboot
```

### 4. Configurar Cámara

#### Para Cámara CSI
```bash
# Verificar que la cámara está conectada
ls -l /dev/video0

# Probar cámara con gstreamer
gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvvidconv ! xvimagesink
```

#### Para Cámara USB
```bash
# Listar dispositivos de video
v4l2-ctl --list-devices

# Probar cámara
ffplay /dev/video0
```

### 5. Verificar Instalación

#### Detectar Dispositivos
```bash
python device_list.py
```

#### Listar Módulos
```bash
python module_manager.py list
```

#### Ejecutar Demo
```bash
python examples/simple_camera.py
```

## Configuración Post-Instalación

### Ajustar Rendimiento

```bash
# Modo máximo rendimiento
sudo nvpmodel -m 0
sudo jetson_clocks

# Verificar status
sudo nvpmodel -q
```

### Configurar Swap (Recomendado)

```bash
# Crear archivo swap de 8GB
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Hacer permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Configurar Arranque Automático

```bash
# Crear servicio systemd
sudo nano /etc/systemd/system/purevision.service
```

Contenido:
```ini
[Unit]
Description=PureVision Service
After=network.target

[Service]
Type=simple
User=jetson
WorkingDirectory=/home/jetson/Documents/Proyectos/purevision
ExecStart=/home/jetson/Documents/Proyectos/purevision/venv/bin/python main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Habilitar:
```bash
sudo systemctl enable purevision
sudo systemctl start purevision
sudo systemctl status purevision
```

## Solución de Problemas

### Error: "No module named 'cv2'"
```bash
# Reinstalar OpenCV
pip install opencv-python

# O verificar ruta de OpenCV compilado
export PYTHONPATH=/usr/local/lib/python3.8/site-packages:$PYTHONPATH
```

### Error: "Cannot open camera"
```bash
# Verificar permisos
sudo chmod 666 /dev/video0

# Verificar que la cámara no está en uso
sudo lsof /dev/video0
```

### Error: "Jetson.GPIO not found"
```bash
# Reinstalar Jetson.GPIO
sudo pip3 install Jetson.GPIO

# Verificar permisos de grupo
groups $USER
```

### Problemas de Rendimiento
```bash
# Aumentar frecuencia
sudo jetson_clocks

# Monitorear recursos
sudo tegrastats

# Reducir resolución en config/camera_module.yaml
```

## Actualización

```bash
cd ~/Documents/Proyectos/purevision
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

## Desinstalación

```bash
# Desactivar servicio (si está configurado)
sudo systemctl stop purevision
sudo systemctl disable purevision
sudo rm /etc/systemd/system/purevision.service

# Eliminar directorio
rm -rf ~/Documents/Proyectos/purevision

# Eliminar entorno virtual
rm -rf ~/Documents/Proyectos/purevision/venv
```

## Soporte

Para problemas de instalación:
- Revisa los logs en `logs/`
- Abre un issue en GitHub
- Consulta la documentación en `docs/`
