"""
FPSCounter - Contador de frames por segundo.
"""

import time
from collections import deque
from typing import Optional


class FPSCounter:
    """
    Contador de FPS con promediado para lecturas estables.
    """
    
    def __init__(self, buffer_size: int = 30):
        """
        Inicializa el contador de FPS.
        
        Args:
            buffer_size: Tamaño del buffer para promediado
        """
        self.buffer_size = buffer_size
        self.timestamps = deque(maxlen=buffer_size)
        self.frame_count = 0
        self.start_time = time.time()
        self.last_time = self.start_time
    
    def tick(self) -> float:
        """
        Registra un nuevo frame y calcula FPS.
        
        Returns:
            FPS actual
        """
        current_time = time.time()
        self.timestamps.append(current_time)
        self.frame_count += 1
        self.last_time = current_time
        
        return self.get_fps()
    
    def get_fps(self) -> float:
        """
        Obtiene el FPS actual (promediado).
        
        Returns:
            FPS promediado
        """
        if len(self.timestamps) < 2:
            return 0.0
        
        # Calcular FPS basado en el buffer
        time_diff = self.timestamps[-1] - self.timestamps[0]
        
        if time_diff > 0:
            return (len(self.timestamps) - 1) / time_diff
        
        return 0.0
    
    def get_average_fps(self) -> float:
        """
        Obtiene el FPS promedio desde el inicio.
        
        Returns:
            FPS promedio total
        """
        elapsed = time.time() - self.start_time
        
        if elapsed > 0:
            return self.frame_count / elapsed
        
        return 0.0
    
    def get_frame_time(self) -> float:
        """
        Obtiene el tiempo del último frame en milisegundos.
        
        Returns:
            Tiempo del frame en ms
        """
        if len(self.timestamps) < 2:
            return 0.0
        
        return (self.timestamps[-1] - self.timestamps[-2]) * 1000
    
    def reset(self) -> None:
        """Reinicia el contador."""
        self.timestamps.clear()
        self.frame_count = 0
        self.start_time = time.time()
        self.last_time = self.start_time
    
    def get_stats(self) -> dict:
        """
        Obtiene estadísticas completas.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            "current_fps": self.get_fps(),
            "average_fps": self.get_average_fps(),
            "frame_count": self.frame_count,
            "frame_time_ms": self.get_frame_time(),
            "elapsed_time": time.time() - self.start_time
        }
