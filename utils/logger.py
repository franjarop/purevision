"""
Logger - Sistema de logging configurado para el proyecto.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


def setup_logger(name: str = "PureVision", level: int = logging.INFO,
                log_to_file: bool = True, log_dir: str = "logs") -> logging.Logger:
    """
    Configura y retorna un logger para el proyecto.
    
    Args:
        name: Nombre del logger
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Si se debe guardar a archivo
        log_dir: Directorio para archivos de log
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Formato de los mensajes
    if COLORLOG_AVAILABLE:
        # Formato con colores para consola
        console_format = (
            "%(log_color)s%(levelname)-8s%(reset)s "
            "%(cyan)s%(name)s%(reset)s - %(message)s"
        )
        console_formatter = colorlog.ColoredFormatter(
            console_format,
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    else:
        # Formato sin colores
        console_format = "%(levelname)-8s %(name)s - %(message)s"
        console_formatter = logging.Formatter(console_format)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"{name}_{timestamp}.log"
        
        file_format = "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s"
        file_formatter = logging.Formatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Logging a archivo: {log_file}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger existente o crea uno nuevo.
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger
    """
    logger = logging.getLogger(name)
    
    # Si no tiene handlers, configurarlo
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


class LoggerContext:
    """
    Context manager para logging temporal con nivel diferente.
    """
    
    def __init__(self, logger: logging.Logger, level: int):
        """
        Inicializa el contexto.
        
        Args:
            logger: Logger a modificar temporalmente
            level: Nivel temporal
        """
        self.logger = logger
        self.new_level = level
        self.old_level = logger.level
    
    def __enter__(self):
        self.logger.setLevel(self.new_level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)


# Logger por defecto del proyecto
_default_logger: Optional[logging.Logger] = None


def get_default_logger() -> logging.Logger:
    """
    Obtiene el logger por defecto del proyecto.
    
    Returns:
        Logger por defecto
    """
    global _default_logger
    
    if _default_logger is None:
        _default_logger = setup_logger("PureVision")
    
    return _default_logger
