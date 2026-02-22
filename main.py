#!/usr/bin/env python3
"""
PureVision - Sistema principal
Script principal para ejecutar el sistema de magnificación euleriana.
"""

import sys
import argparse
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.device_manager import DeviceManager
from core.config_manager import ConfigManager
from core.event_bus import EventBus
from utils.logger import setup_logger
import cv2


def parse_arguments():
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="PureVision - Sistema modular de magnificación euleriana"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/system.yaml",
        help="Archivo de configuración del sistema"
    )
    
    parser.add_argument(
        "--devices-config",
        type=str,
        default="config/devices.yaml",
        help="Archivo de configuración de dispositivos"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Nivel de logging"
    )
    
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Ejecutar sin display (solo procesamiento)"
    )
    
    parser.add_argument(
        "--save-output",
        action="store_true",
        help="Guardar video procesado"
    )
    
    return parser.parse_args()


def main():
    """Función principal."""
    # Parsear argumentos
    args = parse_arguments()
    
    # Configurar logger
    import logging
    log_level = getattr(logging, args.log_level)
    logger = setup_logger("PureVision", level=log_level)
    
    logger.info("=" * 60)
    logger.info("PureVision - Sistema de Magnificación Euleriana")
    logger.info("=" * 60)
    
    try:
        # Cargar configuración
        logger.info("Cargando configuración...")
        config_manager = ConfigManager()
        system_config = config_manager.load_config("system")
        devices_config = config_manager.load_config("devices")
        
        if not system_config or not devices_config:
            logger.error("No se pudo cargar la configuración")
            return 1
        
        # Crear gestor de dispositivos
        logger.info("Inicializando gestor de dispositivos...")
        device_manager = DeviceManager(system_config)
        
        # Descubrir módulos disponibles
        modules = device_manager.discover_modules()
        logger.info(f"Módulos disponibles: {', '.join(modules)}")
        
        # Cargar y crear dispositivos desde configuración
        logger.info("Configurando dispositivos...")
        device_ids = {}
        
        for device_name, device_config in devices_config.get("devices", {}).items():
            if device_config.get("enabled", False):
                module_name = device_config["module"]
                config = device_config.get("config", {})
                
                # Aplicar overrides de argumentos
                if "display" in device_name and args.no_display:
                    config["display_enabled"] = False
                if "display" in device_name and args.save_output:
                    config["save_enabled"] = True
                
                device_id = device_manager.create_device(
                    module_name, device_name, config
                )
                
                if device_id:
                    device_ids[device_name] = device_id
                    logger.info(f"Dispositivo creado: {device_name}")
        
        # Inicializar dispositivos
        logger.info("Inicializando dispositivos...")
        for device_name, device_id in device_ids.items():
            if device_manager.initialize_device(device_id):
                logger.info(f"✓ {device_name} inicializado")
            else:
                logger.error(f"✗ Fallo al inicializar {device_name}")
        
        # Iniciar dispositivos
        logger.info("Iniciando dispositivos...")
        for device_name, device_id in device_ids.items():
            device_manager.start_device(device_id)
        
        # Loop principal
        logger.info("Iniciando loop principal...")
        logger.info("Presiona 'q' para salir")
        
        # Obtener referencias a dispositivos
        camera = device_manager.get_device(device_ids.get("camera_csi_0") or device_ids.get("camera_usb_0"))
        processor = device_manager.get_device(device_ids.get("eulerian_processor"))
        display = device_manager.get_device(device_ids.get("display_main"))
        
        if not camera:
            logger.error("No hay cámara disponible")
            return 1
        
        frame_count = 0
        
        while True:
            # Capturar frame
            frame = camera.process()
            
            if frame is None:
                logger.warning("No se pudo capturar frame")
                continue
            
            frame_count += 1
            
            # Procesar con magnificación euleriana
            if processor:
                processed_frame = processor.process(frame)
            else:
                processed_frame = frame
            
            # Mostrar/guardar
            if display:
                result = display.process(processed_frame)
                
                if result and result.get("action") == "quit":
                    logger.info("Salida solicitada por usuario")
                    break
            
            # Verificar tecla ESC como alternativa
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
        
        logger.info(f"Frames procesados: {frame_count}")
        
    except KeyboardInterrupt:
        logger.info("\nInterrupción por teclado")
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    
    finally:
        # Limpiar
        logger.info("Limpiando recursos...")
        if 'device_manager' in locals():
            device_manager.cleanup_all()
        cv2.destroyAllWindows()
        logger.info("¡Hasta luego!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
