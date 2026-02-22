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

        # Si no hay ninguna cámara marcada como enabled en la configuración,
        # habilitar en memoria la primera cámara USB encontrada (comportamiento deseado)
        try:
            has_enabled_camera = any(
                d.get("enabled", False) and d.get("module") == "camera_module"
                for d in devices_config.get("devices", {}).values()
            )
            if not has_enabled_camera:
                for name, d in devices_config.get("devices", {}).items():
                    if d.get("module") == "camera_module":
                        cfg = d.get("config", {})
                        if cfg.get("camera_type") == "usb":
                            logger.info(f"No hay cámaras habilitadas: habilitando en memoria {name}")
                            d["enabled"] = True
                            break
        except Exception:
            # No bloquear si falla la detección en memoria
            pass
        
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
        initialized_ids = {}
        for device_name, device_id in device_ids.items():
            if device_manager.initialize_device(device_id):
                logger.info(f"✓ {device_name} inicializado")
                initialized_ids[device_name] = device_id
            else:
                logger.error(f"✗ Fallo al inicializar {device_name} — será omitido")
        
        # Iniciar solo dispositivos inicializados correctamente
        logger.info("Iniciando dispositivos...")
        for device_name, device_id in initialized_ids.items():
            device_manager.start_device(device_id)
        
        # Loop principal
        logger.info("Iniciando loop principal...")
        logger.info("Presiona 'q' para salir")
        
        # Obtener referencias a dispositivos (solo de los inicializados)
        camera = device_manager.get_device(initialized_ids.get("camera_csi_0") or initialized_ids.get("camera_usb_0"))
        # Fallback: si no hay cámara (p. ej. CSI no disponible), intentar habilitar la primera cámara USB
        if not camera:
            logger.warning("No se encontró cámara inicial; intentando fallback a cámara USB definida en la configuración")
            # Buscar en la configuración de dispositivos una entrada de tipo camera_module y camera_type usb
            usb_candidate_name = None
            for name, dev in devices_config.get("devices", {}).items():
                if dev.get("module") == "camera_module":
                    cfg = dev.get("config", {})
                    if cfg.get("camera_type") == "usb":
                        usb_candidate_name = name
                        usb_candidate_cfg = cfg
                        break

            if usb_candidate_name:
                # Crear el dispositivo aunque en el YAML esté marcado como disabled
                logger.info(f"Intentando crear dispositivo USB fallback: {usb_candidate_name}")
                created_id = device_manager.create_device("camera_module", usb_candidate_name, usb_candidate_cfg)
                if created_id:
                    if device_manager.initialize_device(created_id):
                        device_manager.start_device(created_id)
                        camera = device_manager.get_device(created_id)
                        if camera:
                            logger.info(f"Cámara USB fallback inicializada: {usb_candidate_name}")
                    else:
                        logger.error("Fallo al inicializar la cámara USB de fallback")
                else:
                    logger.error("No se pudo crear la cámara USB de fallback")
        processor = device_manager.get_device(initialized_ids.get("eulerian_processor"))
        display = device_manager.get_device(initialized_ids.get("display_main"))
        
        if not camera:
            logger.error("No hay cámara disponible")
            return 1
        
        frame_count = 0
        
        # Si no hay display module, crear ventana directa
        if not display:
            logger.info("No hay módulo display activo — mostrando video directamente")
            cv2.namedWindow("PureVision", cv2.WINDOW_NORMAL)
        
        while True:
            # Capturar frame
            frame = camera.process()
            
            if frame is None:
                # Esperar un poco antes de reintentar, evitar CPU al 100%
                key = cv2.waitKey(30) & 0xFF
                if key == ord('q') or key == 27:
                    break
                continue
            
            frame_count += 1
            
            # Procesar con magnificación euleriana
            if processor:
                processed_frame = processor.process(frame)
                if processed_frame is None:
                    processed_frame = frame
            else:
                processed_frame = frame
            
            # Mostrar/guardar
            if display:
                result = display.process(processed_frame)
                
                if result and result.get("action") == "quit":
                    logger.info("Salida solicitada por usuario")
                    break
            else:
                # Mostrar directamente como prueba.py
                cv2.imshow("PureVision", processed_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    logger.info("Salida solicitada por usuario")
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
