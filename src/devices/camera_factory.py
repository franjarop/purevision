"""
CameraFactory - Factory para crear instancias de cámaras según el tipo.
"""

import logging
from typing import Optional, Dict, Any

from .camera_csi_handler import CameraCSIHandler
from .camera_usb_handler import CameraUSBHandler


class CameraFactory:
    """
    Factory para crear handlers de cámara según el tipo y configuración.
    """
    
    @staticmethod
    def create_camera(camera_type: str, config: Dict[str, Any]):
        """
        Crea un handler de cámara según el tipo especificado.
        
        Args:
            camera_type: Tipo de cámara ('csi' o 'usb')
            config: Configuración de la cámara
            
        Returns:
            Handler de cámara apropiado o None si el tipo es inválido
        """
        logger = logging.getLogger("CameraFactory")
        
        if camera_type.lower() == "csi":
            logger.info("Creando handler para cámara CSI")
            return CameraCSIHandler(
                sensor_id=config.get("camera_id", 0),
                width=config.get("width", 1920),
                height=config.get("height", 1080),
                fps=config.get("fps", 30),
                flip_method=config.get("flip_method", 0)
            )
        
        elif camera_type.lower() == "usb":
            logger.info("Creando handler para cámara USB")
            return CameraUSBHandler(
                device_id=config.get("camera_id", 0),
                width=config.get("width", 1920),
                height=config.get("height", 1080),
                fps=config.get("fps", 30),
                backend=config.get("backend", "auto")
            )
        
        else:
            logger.error(f"Tipo de cámara no soportado: {camera_type}")
            return None
    
    @staticmethod
    def detect_cameras() -> Dict[str, Any]:
        """
        Detecta cámaras disponibles en el sistema.
        
        Returns:
            Diccionario con información de cámaras detectadas
        """
        logger = logging.getLogger("CameraFactory")
        detected = {
            "usb_cameras": [],
            "csi_cameras": []
        }
        
        # Detectar cámaras USB
        logger.info("Detectando cámaras USB...")
        for device_id in range(10):  # Probar primeros 10 dispositivos
            try:
                import cv2
                cap = cv2.VideoCapture(device_id)
                if cap.isOpened():
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    
                    detected["usb_cameras"].append({
                        "device_id": device_id,
                        "type": "usb",
                        "default_resolution": f"{width}x{height}",
                        "default_fps": fps
                    })
                    cap.release()
            except Exception as e:
                logger.debug(f"No se pudo abrir /dev/video{device_id}: {e}")
        
        # Detectar cámaras CSI
        logger.info("Detectando cámaras CSI...")
        for sensor_id in range(2):  # Jetson soporta hasta 2 cámaras CSI
            try:
                import cv2
                pipeline = (
                    f"nvarguscamerasrc sensor-id={sensor_id} ! "
                    "video/x-raw(memory:NVMM), width=640, height=480, format=NV12, framerate=30/1 ! "
                    "nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink"
                )
                cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
                if cap.isOpened():
                    detected["csi_cameras"].append({
                        "sensor_id": sensor_id,
                        "type": "csi",
                        "interface": "MIPI CSI-2"
                    })
                    cap.release()
            except Exception as e:
                logger.debug(f"No se pudo abrir CSI sensor {sensor_id}: {e}")
        
        logger.info(f"Detectadas {len(detected['usb_cameras'])} cámaras USB "
                   f"y {len(detected['csi_cameras'])} cámaras CSI")
        
        return detected
