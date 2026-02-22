"""
CameraModule - Módulo para gestión de cámaras CSI/USB en Jetson Nano.
Soporta múltiples tipos de cámaras y proporciona captura de frames.
"""

import cv2
import numpy as np
from typing import Any, Dict, Optional, Tuple
import logging

import sys
sys.path.append('src')

from core.base_device import BaseDevice, DeviceStatus


class CameraModule(BaseDevice):
    """
    Módulo de cámara para Jetson Nano Orin.
    
    Soporta:
    - Cámaras CSI (MIPI CSI-2)
    - Cámaras USB
    - Configuración de resolución y FPS
    - Captura de frames individuales y continua
    """
    
    def __init__(self, device_id: str, config: Dict[str, Any]):
        """
        Inicializa el módulo de cámara.
        
        Args:
            device_id: Identificador único de la cámara
            config: Configuración del dispositivo con:
                - camera_type: 'csi' o 'usb'
                - camera_id: ID de la cámara (0, 1, etc.)
                - width: Ancho de resolución
                - height: Alto de resolución
                - fps: Frames por segundo
                - flip_method: Método de rotación (0-7)
        """
        super().__init__(device_id, config)
        
        self.camera = None
        self.camera_type = config.get("camera_type", "usb")
        self.camera_id = config.get("camera_id", 0)
        self.width = config.get("width", 1920)
        self.height = config.get("height", 1080)
        self.fps = config.get("fps", 30)
        self.flip_method = config.get("flip_method", 0)
        
        self.frame_count = 0
        self.last_frame = None
    
    def initialize(self) -> bool:
        """
        Inicializa la cámara y abre la conexión.
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            self.logger.info(f"Inicializando cámara {self.camera_type} ID {self.camera_id}")
            
            if self.camera_type == "csi":
                # GStreamer pipeline para cámara CSI en Jetson
                gst_pipeline = self._get_csi_pipeline()
                self.camera = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
            else:
                # Cámara USB estándar
                self.camera = cv2.VideoCapture(self.camera_id)
                
                # Configurar resolución y FPS
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            if not self.camera.isOpened():
                self.logger.error("No se pudo abrir la cámara")
                return False
            
            # Verificar que podemos capturar un frame
            ret, frame = self.camera.read()
            if not ret:
                self.logger.error("No se pudo capturar frame de prueba")
                return False
            
            self.last_frame = frame
            self.logger.info(f"Cámara inicializada correctamente: {frame.shape}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al inicializar cámara: {e}")
            return False
    
    def start(self) -> bool:
        """
        Inicia la captura de la cámara.
        
        Returns:
            True si se inició correctamente
        """
        if not self.camera or not self.camera.isOpened():
            self.logger.error("La cámara no está inicializada")
            return False
        
        self.logger.info("Cámara iniciada y lista para capturar")
        return True
    
    def stop(self) -> bool:
        """
        Detiene la captura de la cámara (mantiene conexión).
        
        Returns:
            True si se detuvo correctamente
        """
        self.logger.info("Cámara detenida (conexión mantenida)")
        return True
    
    def process(self, data: Optional[Any] = None) -> Optional[np.ndarray]:
        """
        Captura un frame de la cámara.
        
        Args:
            data: No utilizado para este módulo
            
        Returns:
            Frame capturado como numpy array o None si falla
        """
        if not self.camera or not self.camera.isOpened():
            self.logger.error("La cámara no está disponible")
            return None
        
        ret, frame = self.camera.read()
        
        if not ret:
            self.logger.warning("No se pudo capturar frame")
            return None
        
        self.frame_count += 1
        self.last_frame = frame
        
        return frame
    
    def cleanup(self) -> None:
        """
        Libera los recursos de la cámara.
        """
        if self.camera:
            self.camera.release()
            self.logger.info("Recursos de cámara liberados")
    
    def get_info(self) -> Dict[str, Any]:
        """
        Retorna información de la cámara.
        
        Returns:
            Diccionario con información del dispositivo
        """
        info = {
            "type": "camera",
            "camera_type": self.camera_type,
            "camera_id": self.camera_id,
            "resolution": f"{self.width}x{self.height}",
            "fps": self.fps,
            "frames_captured": self.frame_count,
            "is_opened": self.camera.isOpened() if self.camera else False
        }
        
        if self.camera and self.camera.isOpened():
            info["actual_width"] = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            info["actual_height"] = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            info["actual_fps"] = int(self.camera.get(cv2.CAP_PROP_FPS))
        
        return info
    
    def _get_csi_pipeline(self) -> str:
        """
        Genera el pipeline de GStreamer para cámaras CSI.
        
        Returns:
            String del pipeline de GStreamer
        """
        return (
            f"nvarguscamerasrc sensor-id={self.camera_id} ! "
            f"video/x-raw(memory:NVMM), width={self.width}, height={self.height}, "
            f"format=NV12, framerate={self.fps}/1 ! "
            f"nvvidconv flip-method={self.flip_method} ! "
            f"video/x-raw, width={self.width}, height={self.height}, format=BGRx ! "
            f"videoconvert ! "
            f"video/x-raw, format=BGR ! appsink"
        )
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Método de conveniencia para obtener el último frame.
        
        Returns:
            Último frame capturado
        """
        return self.process()
    
    def get_resolution(self) -> Tuple[int, int]:
        """
        Obtiene la resolución actual de la cámara.
        
        Returns:
            Tupla (ancho, alto)
        """
        if self.camera and self.camera.isOpened():
            width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return (width, height)
        return (self.width, self.height)
    
    def set_resolution(self, width: int, height: int) -> bool:
        """
        Cambia la resolución de la cámara.
        
        Args:
            width: Nuevo ancho
            height: Nueva altura
            
        Returns:
            True si se cambió correctamente
        """
        if self.camera_type == "csi":
            self.logger.warning("No se puede cambiar resolución de cámara CSI en tiempo real")
            return False
        
        if self.camera and self.camera.isOpened():
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            self.width = actual_width
            self.height = actual_height
            
            self.logger.info(f"Resolución cambiada a {actual_width}x{actual_height}")
            return True
        
        return False
