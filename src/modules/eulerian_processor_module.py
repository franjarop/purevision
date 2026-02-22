"""
EulerianProcessorModule - Módulo de procesamiento de magnificación euleriana.
Amplifica movimientos sutiles y variaciones de color en video.
"""

import cv2
import numpy as np
from typing import Any, Dict, Optional
from scipy import signal
import logging

import sys
sys.path.append('src')

from core.base_device import BaseDevice, DeviceStatus


class EulerianProcessorModule(BaseDevice):
    """
    Módulo de magnificación euleriana de video.
    
    Amplifica variaciones temporales sutiles en videos para revelar:
    - Cambios de color (flujo sanguíneo, pulso cardíaco)
    - Movimientos imperceptibles
    - Vibraciones estructurales
    
    Basado en el trabajo del MIT Media Lab:
    "Eulerian Video Magnification for Revealing Subtle Changes in the World"
    """
    
    def __init__(self, device_id: str, config: Dict[str, Any]):
        """
        Inicializa el procesador euleriano.
        
        Args:
            device_id: Identificador único del procesador
            config: Configuración con:
                - amplification_factor: Factor de amplificación (10-150)
                - low_freq: Frecuencia baja del filtro (Hz)
                - high_freq: Frecuencia alta del filtro (Hz)
                - pyramid_levels: Niveles de la pirámide laplaciana (3-6)
                - magnify_type: 'motion' o 'color'
                - fps: FPS del video (para filtrado temporal)
        """
        super().__init__(device_id, config)
        
        # Parámetros de magnificación
        self.amplification_factor = config.get("amplification_factor", 50)
        self.low_freq = config.get("low_freq", 0.4)
        self.high_freq = config.get("high_freq", 3.0)
        self.pyramid_levels = config.get("pyramid_levels", 4)
        self.magnify_type = config.get("magnify_type", "color")
        self.fps = config.get("fps", 30)
        
        # Buffer para almacenar frames procesados
        self.buffer_size = config.get("buffer_size", 150)
        self.frame_buffer = []
        self.pyramid_buffer = []
        
        self.frame_count = 0
        self.processed_frames = 0
    
    def initialize(self) -> bool:
        """
        Inicializa el procesador euleriano.
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            self.logger.info("Inicializando procesador euleriano")
            self.logger.info(f"Configuración: amp={self.amplification_factor}, "
                           f"freq=[{self.low_freq}-{self.high_freq}]Hz, "
                           f"levels={self.pyramid_levels}, type={self.magnify_type}")
            
            # Validar parámetros
            if self.amplification_factor <= 0:
                self.logger.error("Factor de amplificación debe ser positivo")
                return False
            
            if self.low_freq >= self.high_freq:
                self.logger.error("Frecuencia baja debe ser menor que la alta")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al inicializar procesador: {e}")
            return False
    
    def start(self) -> bool:
        """
        Inicia el procesamiento.
        
        Returns:
            True si se inició correctamente
        """
        self.logger.info("Procesador euleriano iniciado")
        return True
    
    def stop(self) -> bool:
        """
        Detiene el procesamiento.
        
        Returns:
            True si se detuvo correctamente
        """
        self.logger.info("Procesador euleriano detenido")
        return True
    
    def process(self, data: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
        """
        Procesa un frame aplicando magnificación euleriana.
        
        Args:
            data: Frame de entrada (numpy array)
            
        Returns:
            Frame magnificado o None si no hay suficientes frames en buffer
        """
        if data is None:
            self.logger.warning("No se recibió frame para procesar")
            return None
        
        try:
            self.frame_count += 1
            
            # Construir pirámide laplaciana del frame
            pyramid = self._build_laplacian_pyramid(data)
            
            # Agregar al buffer
            self.pyramid_buffer.append(pyramid)
            
            # Mantener tamaño del buffer
            if len(self.pyramid_buffer) > self.buffer_size:
                self.pyramid_buffer.pop(0)
            
            # Necesitamos suficientes frames para filtrar
            if len(self.pyramid_buffer) < 30:
                return data  # Retornar frame original hasta tener suficientes
            
            # Aplicar magnificación
            magnified_frame = self._magnify_current_frame(data)
            
            self.processed_frames += 1
            
            return magnified_frame
            
        except Exception as e:
            self.logger.error(f"Error al procesar frame: {e}")
            return data  # Retornar frame original en caso de error
    
    def cleanup(self) -> None:
        """
        Libera recursos del procesador.
        """
        self.frame_buffer.clear()
        self.pyramid_buffer.clear()
        self.logger.info("Recursos del procesador liberados")
    
    def get_info(self) -> Dict[str, Any]:
        """
        Retorna información del procesador.
        
        Returns:
            Diccionario con información del dispositivo
        """
        return {
            "type": "eulerian_processor",
            "amplification_factor": self.amplification_factor,
            "frequency_range": f"{self.low_freq}-{self.high_freq} Hz",
            "pyramid_levels": self.pyramid_levels,
            "magnify_type": self.magnify_type,
            "frames_received": self.frame_count,
            "frames_processed": self.processed_frames,
            "buffer_size": len(self.pyramid_buffer)
        }
    
    def _build_laplacian_pyramid(self, frame: np.ndarray) -> list:
        """
        Construye una pirámide laplaciana del frame.
        
        Args:
            frame: Frame de entrada
            
        Returns:
            Lista con los niveles de la pirámide
        """
        pyramid = [frame.astype(np.float32)]
        
        for level in range(self.pyramid_levels):
            frame = cv2.pyrDown(frame)
            pyramid.append(frame.astype(np.float32))
        
        return pyramid
    
    def _magnify_current_frame(self, original_frame: np.ndarray) -> np.ndarray:
        """
        Aplica magnificación al frame actual usando el buffer.
        
        Args:
            original_frame: Frame original
            
        Returns:
            Frame magnificado
        """
        try:
            # Obtener el índice del frame actual
            current_idx = len(self.pyramid_buffer) - 1
            
            # Para cada nivel de la pirámide
            magnified_pyramid = []
            
            for level in range(len(self.pyramid_buffer[0])):
                # Extraer serie temporal de este nivel
                level_series = np.array([p[level] for p in self.pyramid_buffer])
                
                # Aplicar filtro temporal pasa-banda
                filtered = self._temporal_bandpass_filter(level_series)
                
                # Obtener el frame filtrado actual
                filtered_frame = filtered[current_idx]
                
                # Amplificar
                amplified = filtered_frame * self.amplification_factor
                
                magnified_pyramid.append(amplified)
            
            # Reconstruir frame desde la pirámide magnificada
            magnified_frame = self._reconstruct_from_pyramid(magnified_pyramid)
            
            # Combinar con el frame original
            result = original_frame.astype(np.float32) + magnified_frame
            
            # Clip valores
            result = np.clip(result, 0, 255)
            
            return result.astype(np.uint8)
            
        except Exception as e:
            self.logger.error(f"Error en magnificación: {e}")
            return original_frame
    
    def _temporal_bandpass_filter(self, signal_data: np.ndarray) -> np.ndarray:
        """
        Aplica filtro pasa-banda temporal a la señal.
        
        Args:
            signal_data: Serie temporal de frames
            
        Returns:
            Señal filtrada
        """
        # Diseñar filtro Butterworth pasa-banda
        nyquist = self.fps / 2.0
        low = self.low_freq / nyquist
        high = self.high_freq / nyquist
        
        # Asegurar que los valores estén en el rango válido
        low = max(0.01, min(low, 0.99))
        high = max(low + 0.01, min(high, 0.99))
        
        try:
            b, a = signal.butter(4, [low, high], btype='band')
            
            # Aplicar filtro a cada píxel
            filtered = np.zeros_like(signal_data)
            
            # Filtrar a lo largo del eje temporal (axis=0)
            original_shape = signal_data.shape
            reshaped = signal_data.reshape(original_shape[0], -1)
            
            for i in range(reshaped.shape[1]):
                filtered.reshape(original_shape[0], -1)[:, i] = signal.filtfilt(
                    b, a, reshaped[:, i]
                )
            
            return filtered
            
        except Exception as e:
            self.logger.error(f"Error en filtrado temporal: {e}")
            return signal_data
    
    def _reconstruct_from_pyramid(self, pyramid: list) -> np.ndarray:
        """
        Reconstruye un frame desde una pirámide laplaciana.
        
        Args:
            pyramid: Pirámide laplaciana
            
        Returns:
            Frame reconstruido
        """
        # Comenzar desde el nivel más pequeño
        reconstructed = pyramid[-1]
        
        # Ir expandiendo y sumando niveles
        for level in range(len(pyramid) - 2, -1, -1):
            # Expandir el nivel actual
            reconstructed = cv2.pyrUp(reconstructed)
            
            # Ajustar tamaño si es necesario
            h, w = pyramid[level].shape[:2]
            reconstructed = cv2.resize(reconstructed, (w, h))
            
            # Sumar con el nivel correspondiente
            reconstructed += pyramid[level]
        
        return reconstructed
    
    def set_amplification(self, factor: float) -> None:
        """
        Cambia el factor de amplificación.
        
        Args:
            factor: Nuevo factor de amplificación
        """
        old_factor = self.amplification_factor
        self.amplification_factor = factor
        self.logger.info(f"Factor de amplificación cambiado: {old_factor} -> {factor}")
    
    def set_frequency_range(self, low_freq: float, high_freq: float) -> None:
        """
        Cambia el rango de frecuencias del filtro.
        
        Args:
            low_freq: Nueva frecuencia baja (Hz)
            high_freq: Nueva frecuencia alta (Hz)
        """
        self.low_freq = low_freq
        self.high_freq = high_freq
        self.logger.info(f"Rango de frecuencias cambiado: {low_freq}-{high_freq} Hz")
