"""
Filters - Filtros de procesamiento de imagen y video.
"""

import cv2
import numpy as np
from typing import Tuple, Optional
from scipy import signal


class Filters:
    """
    Colección de filtros para procesamiento de imagen y video.
    """
    
    @staticmethod
    def gaussian_blur(frame: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        """
        Aplica desenfoque gaussiano.
        
        Args:
            frame: Frame de entrada
            kernel_size: Tamaño del kernel (impar)
            
        Returns:
            Frame filtrado
        """
        return cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
    
    @staticmethod
    def bilateral_filter(frame: np.ndarray, d: int = 9, 
                        sigma_color: float = 75, sigma_space: float = 75) -> np.ndarray:
        """
        Aplica filtro bilateral (preserva bordes).
        
        Args:
            frame: Frame de entrada
            d: Diámetro del vecindario
            sigma_color: Sigma en el espacio de color
            sigma_space: Sigma en el espacio de coordenadas
            
        Returns:
            Frame filtrado
        """
        return cv2.bilateralFilter(frame, d, sigma_color, sigma_space)
    
    @staticmethod
    def sharpen(frame: np.ndarray, amount: float = 1.0) -> np.ndarray:
        """
        Aumenta la nitidez de la imagen.
        
        Args:
            frame: Frame de entrada
            amount: Cantidad de nitidez (0.0 - 2.0)
            
        Returns:
            Frame filtrado
        """
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]]) * amount
        return cv2.filter2D(frame, -1, kernel)
    
    @staticmethod
    def edge_detection(frame: np.ndarray, method: str = "canny", 
                      threshold1: float = 100, threshold2: float = 200) -> np.ndarray:
        """
        Detecta bordes en la imagen.
        
        Args:
            frame: Frame de entrada
            method: Método ('canny', 'sobel', 'laplacian')
            threshold1: Umbral inferior (para Canny)
            threshold2: Umbral superior (para Canny)
            
        Returns:
            Imagen de bordes
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        
        if method == "canny":
            return cv2.Canny(gray, threshold1, threshold2)
        elif method == "sobel":
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=5)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)
            return np.sqrt(sobelx**2 + sobely**2).astype(np.uint8)
        elif method == "laplacian":
            return cv2.Laplacian(gray, cv2.CV_64F).astype(np.uint8)
        else:
            return gray
    
    @staticmethod
    def adjust_brightness_contrast(frame: np.ndarray, brightness: float = 0, 
                                   contrast: float = 1.0) -> np.ndarray:
        """
        Ajusta brillo y contraste.
        
        Args:
            frame: Frame de entrada
            brightness: Ajuste de brillo (-100 a 100)
            contrast: Ajuste de contraste (0.5 a 3.0)
            
        Returns:
            Frame ajustado
        """
        adjusted = cv2.convertScaleAbs(frame, alpha=contrast, beta=brightness)
        return adjusted
    
    @staticmethod
    def color_balance(frame: np.ndarray, red_gain: float = 1.0, 
                     green_gain: float = 1.0, blue_gain: float = 1.0) -> np.ndarray:
        """
        Ajusta el balance de color.
        
        Args:
            frame: Frame de entrada (BGR)
            red_gain: Ganancia del canal rojo
            green_gain: Ganancia del canal verde
            blue_gain: Ganancia del canal azul
            
        Returns:
            Frame balanceado
        """
        result = frame.copy().astype(np.float32)
        result[:, :, 0] *= blue_gain
        result[:, :, 1] *= green_gain
        result[:, :, 2] *= red_gain
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    @staticmethod
    def denoise(frame: np.ndarray, method: str = "fastNlMeans", 
               strength: int = 10) -> np.ndarray:
        """
        Reduce el ruido de la imagen.
        
        Args:
            frame: Frame de entrada
            method: Método de denoise ('fastNlMeans', 'bilateral', 'median')
            strength: Fuerza del filtro
            
        Returns:
            Frame filtrado
        """
        if method == "fastNlMeans":
            if len(frame.shape) == 3:
                return cv2.fastNlMeansDenoisingColored(frame, None, strength, strength, 7, 21)
            else:
                return cv2.fastNlMeansDenoising(frame, None, strength, 7, 21)
        elif method == "bilateral":
            return Filters.bilateral_filter(frame, 9, strength, strength)
        elif method == "median":
            return cv2.medianBlur(frame, 5)
        else:
            return frame
    
    @staticmethod
    def temporal_filter(frames: list, method: str = "average") -> np.ndarray:
        """
        Aplica filtrado temporal sobre una secuencia de frames.
        
        Args:
            frames: Lista de frames
            method: Método ('average', 'median', 'gaussian')
            
        Returns:
            Frame filtrado
        """
        if not frames:
            return None
        
        frames_array = np.array(frames, dtype=np.float32)
        
        if method == "average":
            return np.mean(frames_array, axis=0).astype(np.uint8)
        elif method == "median":
            return np.median(frames_array, axis=0).astype(np.uint8)
        elif method == "gaussian":
            # Pesos gaussianos centrados
            n = len(frames)
            sigma = n / 4.0
            weights = signal.gaussian(n, sigma)
            weights /= weights.sum()
            
            result = np.zeros_like(frames[0], dtype=np.float32)
            for i, frame in enumerate(frames):
                result += frame.astype(np.float32) * weights[i]
            
            return result.astype(np.uint8)
        else:
            return frames[-1]
    
    @staticmethod
    def motion_amplification(frame_current: np.ndarray, frame_previous: np.ndarray,
                            amplification: float = 10.0) -> np.ndarray:
        """
        Amplifica las diferencias de movimiento entre dos frames.
        
        Args:
            frame_current: Frame actual
            frame_previous: Frame anterior
            amplification: Factor de amplificación
            
        Returns:
            Frame con movimiento amplificado
        """
        if frame_previous is None:
            return frame_current
        
        # Calcular diferencia
        diff = frame_current.astype(np.float32) - frame_previous.astype(np.float32)
        
        # Amplificar
        amplified_diff = diff * amplification
        
        # Sumar de vuelta al frame original
        result = frame_current.astype(np.float32) + amplified_diff
        
        # Clip y convertir
        result = np.clip(result, 0, 255)
        return result.astype(np.uint8)
    
    @staticmethod
    def resize_maintain_aspect(frame: np.ndarray, target_size: Tuple[int, int],
                               fill_color: Tuple[int, int, int] = (0, 0, 0)) -> np.ndarray:
        """
        Redimensiona manteniendo aspecto y rellenando con color.
        
        Args:
            frame: Frame de entrada
            target_size: Tamaño objetivo (width, height)
            fill_color: Color de relleno (BGR)
            
        Returns:
            Frame redimensionado
        """
        target_w, target_h = target_size
        h, w = frame.shape[:2]
        
        # Calcular escala
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Redimensionar
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # Crear canvas con color de relleno
        canvas = np.full((target_h, target_w, 3), fill_color, dtype=np.uint8)
        
        # Centrar frame redimensionado
        y_offset = (target_h - new_h) // 2
        x_offset = (target_w - new_w) // 2
        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        return canvas
