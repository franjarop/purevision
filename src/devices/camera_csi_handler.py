"""
CameraCSIHandler - Handler específico para cámaras CSI (MIPI CSI-2) en Jetson.
"""

import cv2
import numpy as np
from typing import Optional, Tuple
import logging


class CameraCSIHandler:
    """
    Handler para cámaras CSI conectadas a través de MIPI CSI-2 en Jetson Nano.
    
    Optimizado para:
    - Raspberry Pi Camera Module v2
    - IMX219 sensor
    - IMX477 (HQ Camera)
    """
    
    def __init__(self, sensor_id: int = 0, width: int = 1920, height: int = 1080,
                 fps: int = 30, flip_method: int = 0):
        """
        Inicializa el handler de cámara CSI.
        
        Args:
            sensor_id: ID del sensor CSI (0 o 1)
            width: Ancho de captura
            height: Alto de captura
            fps: Frames por segundo
            flip_method: Método de rotación (0-7)
                0: Sin rotación
                1: Rotar 90° sentido horario
                2: Rotar 180°
                3: Rotar 90° sentido antihorario
                4-7: Variantes con flip
        """
        self.sensor_id = sensor_id
        self.width = width
        self.height = height
        self.fps = fps
        self.flip_method = flip_method
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.capture = None
        self.is_opened = False
    
    def open(self) -> bool:
        """
        Abre la cámara CSI con el pipeline de GStreamer.
        
        Returns:
            True si se abrió correctamente
        """
        try:
            pipeline = self._build_gst_pipeline()
            self.logger.info(f"Abriendo cámara CSI con pipeline: {pipeline}")
            
            self.capture = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            
            if not self.capture.isOpened():
                self.logger.error("No se pudo abrir la cámara CSI")
                return False
            
            self.is_opened = True
            self.logger.info("Cámara CSI abierta correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al abrir cámara CSI: {e}")
            return False
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Lee un frame de la cámara.
        
        Returns:
            Tupla (éxito, frame)
        """
        if not self.is_opened or self.capture is None:
            return False, None
        
        return self.capture.read()
    
    def release(self) -> None:
        """Libera los recursos de la cámara."""
        if self.capture is not None:
            self.capture.release()
            self.is_opened = False
            self.logger.info("Cámara CSI liberada")
    
    def _build_gst_pipeline(self) -> str:
        """
        Construye el pipeline de GStreamer para cámara CSI.
        
        Returns:
            String del pipeline
        """
        return (
            f"nvarguscamerasrc sensor-id={self.sensor_id} ! "
            f"video/x-raw(memory:NVMM), width={self.width}, height={self.height}, "
            f"format=NV12, framerate={self.fps}/1 ! "
            f"nvvidconv flip-method={self.flip_method} ! "
            f"video/x-raw, width={self.width}, height={self.height}, format=BGRx ! "
            f"videoconvert ! "
            f"video/x-raw, format=BGR ! appsink"
        )
    
    def get_property(self, prop: int) -> float:
        """
        Obtiene una propiedad de la cámara.
        
        Args:
            prop: Propiedad de OpenCV (cv2.CAP_PROP_*)
            
        Returns:
            Valor de la propiedad
        """
        if self.capture:
            return self.capture.get(prop)
        return 0.0
    
    def set_property(self, prop: int, value: float) -> bool:
        """
        Establece una propiedad de la cámara.
        
        Args:
            prop: Propiedad de OpenCV (cv2.CAP_PROP_*)
            value: Nuevo valor
            
        Returns:
            True si se estableció correctamente
        """
        if self.capture:
            return self.capture.set(prop, value)
        return False
