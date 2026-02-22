"""
Visualizer - Herramientas de visualización en tiempo real.
"""

import cv2
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
import matplotlib.pyplot as plt
from collections import deque


class Visualizer:
    """
    Herramientas para visualización de datos y video en tiempo real.
    """
    
    def __init__(self, window_name: str = "Visualization"):
        """
        Inicializa el visualizador.
        
        Args:
            window_name: Nombre de la ventana principal
        """
        self.window_name = window_name
        self.signal_buffer = {}
        self.max_buffer_size = 300
    
    @staticmethod
    def draw_text(frame: np.ndarray, text: str, position: Tuple[int, int],
                 font_scale: float = 0.6, color: Tuple[int, int, int] = (0, 255, 0),
                 thickness: int = 2, bg_color: Optional[Tuple[int, int, int]] = None) -> np.ndarray:
        """
        Dibuja texto en un frame con fondo opcional.
        
        Args:
            frame: Frame de entrada
            text: Texto a dibujar
            position: Posición (x, y)
            font_scale: Escala del texto
            color: Color del texto (BGR)
            thickness: Grosor del texto
            bg_color: Color de fondo opcional
            
        Returns:
            Frame con texto dibujado
        """
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Calcular tamaño del texto
        (text_width, text_height), baseline = cv2.getTextSize(
            text, font, font_scale, thickness
        )
        
        x, y = position
        
        # Dibujar fondo si se especifica
        if bg_color is not None:
            padding = 5
            cv2.rectangle(
                frame,
                (x - padding, y - text_height - padding),
                (x + text_width + padding, y + baseline + padding),
                bg_color,
                -1
            )
        
        # Dibujar texto
        cv2.putText(frame, text, (x, y), font, font_scale, color, thickness)
        
        return frame
    
    @staticmethod
    def draw_fps(frame: np.ndarray, fps: float, position: Tuple[int, int] = (10, 30)) -> np.ndarray:
        """
        Dibuja FPS en el frame.
        
        Args:
            frame: Frame de entrada
            fps: Valor de FPS
            position: Posición del texto
            
        Returns:
            Frame con FPS dibujado
        """
        text = f"FPS: {fps:.1f}"
        color = (0, 255, 0) if fps >= 25 else (0, 165, 255) if fps >= 15 else (0, 0, 255)
        return Visualizer.draw_text(frame, text, position, color=color, bg_color=(0, 0, 0))
    
    @staticmethod
    def draw_grid(frame: np.ndarray, rows: int = 3, cols: int = 3,
                 color: Tuple[int, int, int] = (100, 100, 100),
                 thickness: int = 1) -> np.ndarray:
        """
        Dibuja una rejilla en el frame.
        
        Args:
            frame: Frame de entrada
            rows: Número de filas
            cols: Número de columnas
            color: Color de las líneas
            thickness: Grosor de las líneas
            
        Returns:
            Frame con rejilla
        """
        h, w = frame.shape[:2]
        result = frame.copy()
        
        # Líneas horizontales
        for i in range(1, rows):
            y = int(h * i / rows)
            cv2.line(result, (0, y), (w, y), color, thickness)
        
        # Líneas verticales
        for i in range(1, cols):
            x = int(w * i / cols)
            cv2.line(result, (x, 0), (x, h), color, thickness)
        
        return result
    
    @staticmethod
    def draw_roi(frame: np.ndarray, roi: Tuple[int, int, int, int],
                color: Tuple[int, int, int] = (0, 255, 0),
                thickness: int = 2, label: Optional[str] = None) -> np.ndarray:
        """
        Dibuja una región de interés (ROI).
        
        Args:
            frame: Frame de entrada
            roi: Región (x, y, width, height)
            color: Color del rectángulo
            thickness: Grosor de las líneas
            label: Etiqueta opcional
            
        Returns:
            Frame con ROI dibujado
        """
        x, y, w, h = roi
        result = frame.copy()
        
        cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
        
        if label:
            Visualizer.draw_text(result, label, (x, y - 5), color=color, bg_color=(0, 0, 0))
        
        return result
    
    def add_signal_point(self, signal_name: str, value: float) -> None:
        """
        Añade un punto a una señal temporal.
        
        Args:
            signal_name: Nombre de la señal
            value: Valor del punto
        """
        if signal_name not in self.signal_buffer:
            self.signal_buffer[signal_name] = deque(maxlen=self.max_buffer_size)
        
        self.signal_buffer[signal_name].append(value)
    
    def plot_signals(self, signals: Optional[List[str]] = None,
                    title: str = "Signals", size: Tuple[int, int] = (800, 400)) -> np.ndarray:
        """
        Genera una imagen con el gráfico de señales temporales.
        
        Args:
            signals: Lista de nombres de señales a graficar (None = todas)
            title: Título del gráfico
            size: Tamaño de la imagen (width, height)
            
        Returns:
            Imagen del gráfico
        """
        if signals is None:
            signals = list(self.signal_buffer.keys())
        
        # Crear figura de matplotlib
        fig, ax = plt.subplots(figsize=(size[0]/100, size[1]/100), dpi=100)
        
        for signal_name in signals:
            if signal_name in self.signal_buffer:
                data = list(self.signal_buffer[signal_name])
                ax.plot(data, label=signal_name)
        
        ax.set_title(title)
        ax.set_xlabel("Time")
        ax.set_ylabel("Value")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Convertir a imagen numpy
        fig.canvas.draw()
        img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        img = img.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        
        plt.close(fig)
        
        # Convertir RGB a BGR para OpenCV
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    @staticmethod
    def create_side_by_side(frame1: np.ndarray, frame2: np.ndarray,
                           labels: Optional[Tuple[str, str]] = None) -> np.ndarray:
        """
        Crea una visualización lado a lado de dos frames.
        
        Args:
            frame1: Primer frame
            frame2: Segundo frame
            labels: Etiquetas opcionales (label1, label2)
            
        Returns:
            Imagen combinada
        """
        # Asegurar mismo tamaño
        h1, w1 = frame1.shape[:2]
        h2, w2 = frame2.shape[:2]
        
        target_h = max(h1, h2)
        
        if h1 != target_h:
            frame1 = cv2.resize(frame1, (int(w1 * target_h / h1), target_h))
        if h2 != target_h:
            frame2 = cv2.resize(frame2, (int(w2 * target_h / h2), target_h))
        
        # Añadir etiquetas si se proporcionan
        if labels:
            frame1 = Visualizer.draw_text(
                frame1, labels[0], (10, 30),
                font_scale=1.0, color=(255, 255, 255), bg_color=(0, 0, 0)
            )
            frame2 = Visualizer.draw_text(
                frame2, labels[1], (10, 30),
                font_scale=1.0, color=(255, 255, 255), bg_color=(0, 0, 0)
            )
        
        # Concatenar horizontalmente
        return np.hstack([frame1, frame2])
    
    @staticmethod
    def create_mosaic(frames: List[np.ndarray], grid_size: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """
        Crea un mosaico de múltiples frames.
        
        Args:
            frames: Lista de frames
            grid_size: Tamaño de la rejilla (rows, cols). None = automático
            
        Returns:
            Mosaico de frames
        """
        n_frames = len(frames)
        if n_frames == 0:
            return np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Determinar tamaño de rejilla
        if grid_size is None:
            cols = int(np.ceil(np.sqrt(n_frames)))
            rows = int(np.ceil(n_frames / cols))
        else:
            rows, cols = grid_size
        
        # Redimensionar frames al mismo tamaño
        target_h = frames[0].shape[0] // rows
        target_w = frames[0].shape[1] // cols
        
        resized_frames = []
        for frame in frames:
            resized = cv2.resize(frame, (target_w, target_h))
            resized_frames.append(resized)
        
        # Rellenar con frames negros si es necesario
        while len(resized_frames) < rows * cols:
            resized_frames.append(np.zeros((target_h, target_w, 3), dtype=np.uint8))
        
        # Crear mosaico
        mosaic_rows = []
        for i in range(rows):
            row_frames = resized_frames[i*cols:(i+1)*cols]
            mosaic_rows.append(np.hstack(row_frames))
        
        return np.vstack(mosaic_rows)
