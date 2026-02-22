#!/usr/bin/env python3
"""
simple_camera.py - Ejemplo básico de uso del módulo de cámara.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modules.camera_module import CameraModule
import cv2


def main():
    """Ejemplo simple de captura de cámara."""
    print("Ejemplo: Captura simple de cámara")
    print("Presiona 'q' para salir\n")
    
    # Configuración de cámara
    config = {
        "camera_type": "usb",  # Cambiar a "csi" para cámara CSI
        "camera_id": 0,
        "width": 1280,
        "height": 720,
        "fps": 30
    }
    
    # Crear módulo de cámara
    camera = CameraModule("camera_example", config)
    
    # Inicializar
    if not camera.initialize():
        print("Error: No se pudo inicializar la cámara")
        return 1
    
    # Iniciar
    camera.start()
    
    # Obtener información
    info = camera.get_info()
    print(f"Cámara: {info['camera_type']}")
    print(f"Resolución: {info['resolution']}")
    print(f"FPS: {info['fps']}\n")
    
    # Loop de captura
    frame_count = 0
    
    try:
        while True:
            # Capturar frame
            frame = camera.process()
            
            if frame is None:
                print("No se pudo capturar frame")
                continue
            
            frame_count += 1
            
            # Mostrar información en frame
            cv2.putText(frame, f"Frame: {frame_count}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Mostrar
            cv2.imshow("Simple Camera Example", frame)
            
            # Salir con 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("\nInterrumpido")
    
    finally:
        # Limpiar
        camera.stop()
        camera.cleanup()
        cv2.destroyAllWindows()
        print(f"\nFrames capturados: {frame_count}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
