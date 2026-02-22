"""
CameraUSBHandler - Handler específico para cámaras USB estándar.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List
import logging


class CameraUSBHandler:
    """
    Handler para cámaras USB estándar (UVC).
    
    Soporta cualquier cámara USB compatible con V4L2.
    """
    
    def __init__(self, device_id: int = 0, width: int = 1920, height: int = 1080,
                 fps: int = 30, backend: str = "auto"):
        """
        Inicializa el handler de cámara USB.
        
        Args:
            device_id: ID del dispositivo (/dev/video<id>)
            width: Ancho de captura
            height: Alto de captura
            fps: Frames por segundo
            backend: Backend de captura ('auto', 'v4l2', 'gstreamer')
        """
        self.device_id = device_id
        self.width = width
        self.height = height
        self.fps = fps
        self.backend = backend
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.capture = None
        self.is_opened = False
    
    def open(self) -> bool:
        """
        Abre la cámara USB.
        
        Returns:
            True si se abrió correctamente
        """
        try:
            self.logger.info(f"Abriendo cámara USB {self.device_id}")
            
            # Seleccionar backend
            if self.backend == "v4l2":
                self.capture = cv2.VideoCapture(self.device_id, cv2.CAP_V4L2)
            elif self.backend == "gstreamer":
                pipeline = self._build_gst_pipeline()
                self.capture = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            else:
                self.capture = cv2.VideoCapture(self.device_id)
            
            if not self.capture.isOpened():
                self.logger.error("No se pudo abrir la cámara USB")
                return False
            
            # Configurar propiedades
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Verificar propiedades reales
            actual_width = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = self.capture.get(cv2.CAP_PROP_FPS)
            
            self.logger.info(f"Cámara USB abierta: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            self.is_opened = True
            return True
            
        except Exception as e:
            self.logger.error(f"Error al abrir cámara USB: {e}")
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
            self.logger.info("Cámara USB liberada")
    
    def _build_gst_pipeline(self) -> str:
        """
        Construye un pipeline de GStreamer para cámara USB.
        
        Returns:
            String del pipeline
        """
        return (
            f"v4l2src device=/dev/video{self.device_id} ! "
            f"video/x-raw, width={self.width}, height={self.height}, "
            f"framerate={self.fps}/1 ! "
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
            result = self.capture.set(prop, value)
            if result:
                self.logger.debug(f"Propiedad {prop} establecida a {value}")
            return result
        return False
    
    def list_supported_resolutions(self) -> List[Tuple[int, int]]:
        """
        Lista las resoluciones soportadas por la cámara.
        
        Returns:
            Lista de tuplas (ancho, alto)
        """
        # Resoluciones comunes a probar
        common_resolutions = [
            (640, 480),
            (800, 600),
            (1280, 720),
            (1920, 1080),
            (2560, 1440),
            (3840, 2160),
        ]
        
        supported = []
        
        for width, height in common_resolutions:
            test_cap = cv2.VideoCapture(self.device_id)
            test_cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            test_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            actual_width = int(test_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(test_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if actual_width == width and actual_height == height:
                supported.append((width, height))
            
            test_cap.release()
        
        return supported
    
    def set_auto_exposure(self, enable: bool) -> bool:
        """
        Habilita o deshabilita la exposición automática.
        
        Args:
            enable: True para auto, False para manual
            
        Returns:
            True si se configuró correctamente
        """
        if enable:
            return self.set_property(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
        else:
            return self.set_property(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
    
    def set_exposure(self, value: float) -> bool:
        """
        Establece el valor de exposición manual.
        
        Args:
            value: Valor de exposición (rango depende de la cámara)
            
        Returns:
            True si se configuró correctamente
        """
        # Primero deshabilitar auto-exposición
        self.set_auto_exposure(False)
        return self.set_property(cv2.CAP_PROP_EXPOSURE, value)
