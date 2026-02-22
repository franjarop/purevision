"""
DisplayModule - Módulo para visualización y salida de video.
Muestra frames procesados en ventanas o guarda a archivo.
"""

import cv2
import numpy as np
from typing import Any, Dict, Optional
import logging
from datetime import datetime
from pathlib import Path

import sys
sys.path.append('src')

from core.base_device import BaseDevice, DeviceStatus


class DisplayModule(BaseDevice):
    """
    Módulo de visualización y salida de video.
    
    Soporta:
    - Mostrar video en ventana
    - Guardar video a archivo
    - Capturar frames individuales
    - Overlay de información
    """
    
    def __init__(self, device_id: str, config: Dict[str, Any]):
        """
        Inicializa el módulo de display.
        
        Args:
            device_id: Identificador único del display
            config: Configuración con:
                - window_name: Nombre de la ventana
                - display_enabled: Mostrar ventana
                - save_enabled: Guardar a archivo
                - output_path: Ruta de salida para videos
                - codec: Codec de video (ej: 'XVID', 'mp4v')
                - fps: FPS para guardar video
                - show_fps: Mostrar FPS en pantalla
                - show_info: Mostrar información overlay
        """
        super().__init__(device_id, config)
        
        self.window_name = config.get("window_name", "PureVision")
        self.display_enabled = config.get("display_enabled", True)
        self.save_enabled = config.get("save_enabled", False)
        self.output_path = Path(config.get("output_path", "output"))
        self.codec = config.get("codec", "mp4v")
        self.fps = config.get("fps", 30)
        self.show_fps = config.get("show_fps", True)
        self.show_info = config.get("show_info", True)
        
        self.video_writer = None
        self.frame_count = 0
        self.current_fps = 0
        
        # Para cálculo de FPS
        import time
        self.last_time = time.time()
        self.fps_buffer = []
    
    def initialize(self) -> bool:
        """
        Inicializa el módulo de display.
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            self.logger.info("Inicializando módulo de display")
            
            # Crear directorio de salida si es necesario
            if self.save_enabled:
                self.output_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Directorio de salida: {self.output_path}")
            
            # Crear ventana si está habilitada
            if self.display_enabled:
                cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
                self.logger.info(f"Ventana creada: {self.window_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al inicializar display: {e}")
            return False
    
    def start(self) -> bool:
        """
        Inicia el display.
        
        Returns:
            True si se inició correctamente
        """
        if self.save_enabled and self.video_writer is None:
            # Crear writer de video
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_path / f"output_{timestamp}.avi"
            
            fourcc = cv2.VideoWriter_fourcc(*self.codec)
            # Tamaño se establecerá con el primer frame
            self.logger.info(f"Preparado para guardar video: {output_file}")
        
        self.logger.info("Display iniciado")
        return True
    
    def stop(self) -> bool:
        """
        Detiene el display.
        
        Returns:
            True si se detuvo correctamente
        """
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
            self.logger.info("Video guardado y writer liberado")
        
        self.logger.info("Display detenido")
        return True
    
    def process(self, data: Optional[np.ndarray] = None) -> Optional[Dict[str, Any]]:
        """
        Muestra un frame y/o lo guarda.
        
        Args:
            data: Frame a mostrar (numpy array)
            
        Returns:
            Información sobre la operación
        """
        if data is None:
            return None
        
        try:
            frame = data.copy()
            self.frame_count += 1
            
            # Calcular FPS
            self._update_fps()
            
            # Agregar overlays si está habilitado
            if self.show_fps or self.show_info:
                frame = self._add_overlays(frame)
            
            # Mostrar en ventana
            if self.display_enabled:
                cv2.imshow(self.window_name, frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    return {"action": "quit", "frame_count": self.frame_count}
                elif key == ord('s'):
                    self._save_snapshot(frame)
            
            # Guardar a video
            if self.save_enabled:
                self._write_frame(frame)
            
            return {
                "frame_count": self.frame_count,
                "fps": self.current_fps
            }
            
        except Exception as e:
            self.logger.error(f"Error al procesar frame: {e}")
            return None
    
    def cleanup(self) -> None:
        """
        Libera recursos del display.
        """
        if self.video_writer is not None:
            self.video_writer.release()
        
        if self.display_enabled:
            cv2.destroyWindow(self.window_name)
        
        self.logger.info("Recursos de display liberados")
    
    def get_info(self) -> Dict[str, Any]:
        """
        Retorna información del display.
        
        Returns:
            Diccionario con información del dispositivo
        """
        return {
            "type": "display",
            "window_name": self.window_name,
            "display_enabled": self.display_enabled,
            "save_enabled": self.save_enabled,
            "frames_displayed": self.frame_count,
            "current_fps": self.current_fps,
            "output_path": str(self.output_path)
        }
    
    def _update_fps(self) -> None:
        """Actualiza el cálculo de FPS."""
        import time
        current_time = time.time()
        elapsed = current_time - self.last_time
        
        if elapsed > 0:
            fps = 1.0 / elapsed
            self.fps_buffer.append(fps)
            
            # Mantener buffer de últimos 30 frames
            if len(self.fps_buffer) > 30:
                self.fps_buffer.pop(0)
            
            # Promediar
            self.current_fps = sum(self.fps_buffer) / len(self.fps_buffer)
        
        self.last_time = current_time
    
    def _add_overlays(self, frame: np.ndarray) -> np.ndarray:
        """
        Agrega información superpuesta al frame.
        
        Args:
            frame: Frame original
            
        Returns:
            Frame con overlays
        """
        overlay_frame = frame.copy()
        
        # Parámetros de texto
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        color = (0, 255, 0)  # Verde
        y_offset = 30
        
        # FPS
        if self.show_fps:
            fps_text = f"FPS: {self.current_fps:.1f}"
            cv2.putText(overlay_frame, fps_text, (10, y_offset), 
                       font, font_scale, color, thickness)
            y_offset += 30
        
        # Frame count
        if self.show_info:
            frame_text = f"Frame: {self.frame_count}"
            cv2.putText(overlay_frame, frame_text, (10, y_offset), 
                       font, font_scale, color, thickness)
            y_offset += 30
            
            # Timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            cv2.putText(overlay_frame, timestamp, (10, y_offset), 
                       font, font_scale, color, thickness)
        
        return overlay_frame
    
    def _write_frame(self, frame: np.ndarray) -> None:
        """
        Escribe un frame al video de salida.
        
        Args:
            frame: Frame a escribir
        """
        if self.video_writer is None:
            # Inicializar writer con el tamaño del primer frame
            h, w = frame.shape[:2]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_path / f"output_{timestamp}.avi"
            
            fourcc = cv2.VideoWriter_fourcc(*self.codec)
            self.video_writer = cv2.VideoWriter(
                str(output_file), fourcc, self.fps, (w, h)
            )
            self.logger.info(f"VideoWriter creado: {output_file}")
        
        self.video_writer.write(frame)
    
    def _save_snapshot(self, frame: np.ndarray) -> None:
        """
        Guarda un snapshot del frame actual.
        
        Args:
            frame: Frame a guardar
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_file = self.output_path / f"snapshot_{timestamp}.png"
        
        cv2.imwrite(str(snapshot_file), frame)
        self.logger.info(f"Snapshot guardado: {snapshot_file}")
    
    def set_window_title(self, title: str) -> None:
        """
        Cambia el título de la ventana.
        
        Args:
            title: Nuevo título
        """
        if self.display_enabled:
            cv2.setWindowTitle(self.window_name, title)
