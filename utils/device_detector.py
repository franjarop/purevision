"""
DeviceDetector - Detecta dispositivos conectados al sistema.
"""

import subprocess
import logging
from typing import List, Dict, Any
import platform


class DeviceDetector:
    """
    Detector de dispositivos hardware conectados al sistema.
    """
    
    def __init__(self):
        """Inicializa el detector de dispositivos."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.system = platform.system()
    
    def detect_all(self) -> Dict[str, Any]:
        """
        Detecta todos los dispositivos disponibles.
        
        Returns:
            Diccionario con información de dispositivos detectados
        """
        self.logger.info("Detectando dispositivos...")
        
        devices = {
            "cameras": self.detect_cameras(),
            "usb_devices": self.detect_usb_devices(),
            "i2c_devices": self.detect_i2c_devices(),
            "gpio_available": self.check_gpio_available(),
            "system_info": self.get_system_info()
        }
        
        return devices
    
    def detect_cameras(self) -> List[Dict[str, Any]]:
        """
        Detecta cámaras disponibles.
        
        Returns:
            Lista de cámaras detectadas
        """
        cameras = []
        
        try:
            import cv2
            
            # Detectar cámaras USB (V4L2)
            for i in range(10):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    
                    cameras.append({
                        "type": "usb",
                        "id": i,
                        "device": f"/dev/video{i}",
                        "resolution": f"{width}x{height}",
                        "fps": fps
                    })
                    cap.release()
            
            # Detectar cámaras CSI (Jetson)
            if self._is_jetson():
                for sensor_id in range(2):
                    if self._test_csi_camera(sensor_id):
                        cameras.append({
                            "type": "csi",
                            "id": sensor_id,
                            "interface": "MIPI CSI-2",
                            "device": f"CSI-{sensor_id}"
                        })
            
            self.logger.info(f"Detectadas {len(cameras)} cámaras")
            
        except Exception as e:
            self.logger.error(f"Error al detectar cámaras: {e}")
        
        return cameras
    
    def detect_usb_devices(self) -> List[Dict[str, Any]]:
        """
        Detecta dispositivos USB conectados.
        
        Returns:
            Lista de dispositivos USB
        """
        devices = []
        
        try:
            if self.system == "Linux":
                result = subprocess.run(
                    ["lsusb"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            devices.append({"info": line})
            
            self.logger.info(f"Detectados {len(devices)} dispositivos USB")
            
        except Exception as e:
            self.logger.error(f"Error al detectar dispositivos USB: {e}")
        
        return devices
    
    def detect_i2c_devices(self) -> List[Dict[str, Any]]:
        """
        Detecta dispositivos I2C conectados.
        
        Returns:
            Lista de dispositivos I2C
        """
        devices = []
        
        try:
            if self.system == "Linux":
                # Intentar con i2cdetect
                for bus in range(8):
                    try:
                        result = subprocess.run(
                            ["i2cdetect", "-y", str(bus)],
                            capture_output=True,
                            text=True,
                            timeout=2
                        )
                        
                        if result.returncode == 0:
                            # Parsear salida de i2cdetect
                            addresses = self._parse_i2cdetect(result.stdout)
                            if addresses:
                                devices.append({
                                    "bus": bus,
                                    "addresses": addresses
                                })
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        pass
            
            self.logger.info(f"Detectados dispositivos I2C en {len(devices)} buses")
            
        except Exception as e:
            self.logger.error(f"Error al detectar dispositivos I2C: {e}")
        
        return devices
    
    def check_gpio_available(self) -> bool:
        """
        Verifica si GPIO está disponible.
        
        Returns:
            True si GPIO está disponible
        """
        try:
            if self._is_jetson():
                import Jetson.GPIO as GPIO
                return True
        except ImportError:
            pass
        
        try:
            import RPi.GPIO as GPIO
            return True
        except ImportError:
            pass
        
        return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Obtiene información del sistema.
        
        Returns:
            Diccionario con información del sistema
        """
        info = {
            "platform": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }
        
        # Información específica de Jetson
        if self._is_jetson():
            info["jetson"] = self._get_jetson_info()
        
        return info
    
    def _is_jetson(self) -> bool:
        """
        Verifica si el sistema es una Jetson.
        
        Returns:
            True si es Jetson
        """
        try:
            with open("/etc/nv_tegra_release", "r") as f:
                return "tegra" in f.read().lower()
        except FileNotFoundError:
            return False
    
    def _get_jetson_info(self) -> Dict[str, str]:
        """
        Obtiene información específica de Jetson.
        
        Returns:
            Información de Jetson
        """
        info = {}
        
        try:
            # Leer versión de JetPack
            result = subprocess.run(
                ["dpkg", "-l", "nvidia-jetpack"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'nvidia-jetpack' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            info["jetpack_version"] = parts[2]
            
            # Leer modelo
            with open("/proc/device-tree/model", "r") as f:
                info["model"] = f.read().strip().replace('\x00', '')
        
        except Exception as e:
            self.logger.debug(f"Error al obtener info de Jetson: {e}")
        
        return info
    
    def _test_csi_camera(self, sensor_id: int) -> bool:
        """
        Prueba si una cámara CSI está disponible.
        
        Args:
            sensor_id: ID del sensor
            
        Returns:
            True si la cámara está disponible
        """
        try:
            import cv2
            pipeline = (
                f"nvarguscamerasrc sensor-id={sensor_id} num-buffers=1 ! "
                "video/x-raw(memory:NVMM), width=640, height=480, format=NV12 ! "
                "nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! "
                "video/x-raw, format=BGR ! appsink"
            )
            cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            is_opened = cap.isOpened()
            cap.release()
            return is_opened
        except Exception:
            return False
    
    def _parse_i2cdetect(self, output: str) -> List[str]:
        """
        Parsea la salida de i2cdetect.
        
        Args:
            output: Salida del comando
            
        Returns:
            Lista de direcciones detectadas
        """
        addresses = []
        
        for line in output.split('\n'):
            # Buscar líneas con direcciones (contienen :)
            if ':' in line:
                parts = line.split(':')[1].strip().split()
                for part in parts:
                    if part != '--' and len(part) == 2:
                        addresses.append(part)
        
        return addresses
