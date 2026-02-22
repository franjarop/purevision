"""
VideoPipeline - Pipeline completo de procesamiento de video.
Coordina la captura, procesamiento y salida de video.
"""

import logging
from typing import Optional, Dict, Any, Callable
import numpy as np
import time


class VideoPipeline:
    """
    Pipeline de procesamiento de video que coordina múltiples etapas.
    
    Permite encadenar múltiples procesadores de forma eficiente.
    """
    
    def __init__(self, name: str = "VideoPipeline"):
        """
        Inicializa el pipeline de video.
        
        Args:
            name: Nombre del pipeline
        """
        self.name = name
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.stages = []
        self.stats = {
            "frames_processed": 0,
            "total_time": 0.0,
            "average_fps": 0.0
        }
    
    def add_stage(self, name: str, processor: Callable, enabled: bool = True) -> None:
        """
        Añade una etapa al pipeline.
        
        Args:
            name: Nombre de la etapa
            processor: Función o callable que procesa el frame
            enabled: Si la etapa está habilitada
        """
        self.stages.append({
            "name": name,
            "processor": processor,
            "enabled": enabled,
            "execution_time": 0.0,
            "frame_count": 0
        })
        self.logger.info(f"Etapa añadida: {name}")
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Procesa un frame a través de todas las etapas del pipeline.
        
        Args:
            frame: Frame de entrada
            
        Returns:
            Frame procesado
        """
        start_time = time.time()
        
        result = frame
        
        for stage in self.stages:
            if not stage["enabled"]:
                continue
            
            try:
                stage_start = time.time()
                result = stage["processor"](result)
                stage_time = time.time() - stage_start
                
                stage["execution_time"] += stage_time
                stage["frame_count"] += 1
                
            except Exception as e:
                self.logger.error(f"Error en etapa {stage['name']}: {e}")
                # Continuar con el frame sin procesar de esta etapa
        
        # Actualizar estadísticas globales
        total_time = time.time() - start_time
        self.stats["frames_processed"] += 1
        self.stats["total_time"] += total_time
        
        if self.stats["total_time"] > 0:
            self.stats["average_fps"] = self.stats["frames_processed"] / self.stats["total_time"]
        
        return result
    
    def enable_stage(self, name: str) -> bool:
        """
        Habilita una etapa del pipeline.
        
        Args:
            name: Nombre de la etapa
            
        Returns:
            True si se encontró y habilitó la etapa
        """
        for stage in self.stages:
            if stage["name"] == name:
                stage["enabled"] = True
                self.logger.info(f"Etapa habilitada: {name}")
                return True
        return False
    
    def disable_stage(self, name: str) -> bool:
        """
        Deshabilita una etapa del pipeline.
        
        Args:
            name: Nombre de la etapa
            
        Returns:
            True si se encontró y deshabilitó la etapa
        """
        for stage in self.stages:
            if stage["name"] == name:
                stage["enabled"] = False
                self.logger.info(f"Etapa deshabilitada: {name}")
                return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del pipeline.
        
        Returns:
            Diccionario con estadísticas
        """
        stage_stats = []
        for stage in self.stages:
            if stage["frame_count"] > 0:
                avg_time = stage["execution_time"] / stage["frame_count"]
                stage_stats.append({
                    "name": stage["name"],
                    "enabled": stage["enabled"],
                    "frames_processed": stage["frame_count"],
                    "average_time_ms": avg_time * 1000,
                    "percentage": (stage["execution_time"] / self.stats["total_time"]) * 100
                        if self.stats["total_time"] > 0 else 0
                })
        
        return {
            "pipeline_name": self.name,
            "total_frames": self.stats["frames_processed"],
            "average_fps": self.stats["average_fps"],
            "stages": stage_stats
        }
    
    def reset_stats(self) -> None:
        """Reinicia las estadísticas del pipeline."""
        self.stats = {
            "frames_processed": 0,
            "total_time": 0.0,
            "average_fps": 0.0
        }
        
        for stage in self.stages:
            stage["execution_time"] = 0.0
            stage["frame_count"] = 0
        
        self.logger.info("Estadísticas reiniciadas")
    
    def clear_stages(self) -> None:
        """Elimina todas las etapas del pipeline."""
        self.stages.clear()
        self.reset_stats()
        self.logger.info("Pipeline limpiado")
