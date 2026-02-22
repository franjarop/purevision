#!/usr/bin/env python3
"""
eulerian_realtime.py - Demo completa de magnificación euleriana en tiempo real.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modules.camera_module import CameraModule
from modules.eulerian_processor_module import EulerianProcessorModule
from modules.display_module import DisplayModule
from utils.fps_counter import FPSCounter
from utils.visualizer import Visualizer
import cv2
import numpy as np


def main():
    """Demo completa de magnificación euleriana."""
    print("=" * 60)
    print("Demo: Magnificación Euleriana en Tiempo Real")
    print("=" * 60)
    print("\nControles:")
    print("  q - Salir")
    print("  s - Guardar snapshot")
    print("  1 - Preset: Detección de pulso")
    print("  2 - Preset: Amplificación de movimiento")
    print("  3 - Preset: Detección de respiración")
    print("  + - Aumentar amplificación")
    print("  - - Disminuir amplificación")
    print()
    
    # Configuración de cámara
    camera_config = {
        "camera_type": "usb",
        "camera_id": 0,
        "width": 640,
        "height": 480,
        "fps": 30
    }
    
    # Configuración de procesador euleriano
    processor_config = {
        "amplification_factor": 50,
        "low_freq": 0.4,
        "high_freq": 3.0,
        "pyramid_levels": 4,
        "magnify_type": "color",
        "fps": 30,
        "buffer_size": 150
    }
    
    # Configuración de display
    display_config = {
        "window_name": "Eulerian Magnification Demo",
        "display_enabled": True,
        "save_enabled": False,
        "show_fps": True,
        "show_info": True
    }
    
    # Crear módulos
    camera = CameraModule("demo_camera", camera_config)
    processor = EulerianProcessorModule("demo_processor", processor_config)
    display = DisplayModule("demo_display", display_config)
    
    # Inicializar
    if not all([camera.initialize(), processor.initialize(), display.initialize()]):
        print("Error al inicializar módulos")
        return 1
    
    # Iniciar
    camera.start()
    processor.start()
    display.start()
    
    print("Sistema iniciado. Capturando...")
    
    # FPS counter
    fps_counter = FPSCounter()
    visualizer = Visualizer()
    
    frame_count = 0
    
    try:
        while True:
            # Capturar
            frame = camera.process()
            if frame is None:
                continue
            
            frame_count += 1
            fps = fps_counter.tick()
            
            # Procesar magnificación
            magnified = processor.process(frame)
            
            # Crear visualización lado a lado
            combined = visualizer.create_side_by_side(
                frame, magnified,
                labels=("Original", "Magnificado")
            )
            
            # Agregar información
            info_text = [
                f"FPS: {fps:.1f}",
                f"Frames: {frame_count}",
                f"Amplificación: {processor.amplification_factor}",
                f"Frecuencia: {processor.low_freq}-{processor.high_freq} Hz"
            ]
            
            y_offset = 30
            for text in info_text:
                combined = visualizer.draw_text(
                    combined, text, (10, y_offset),
                    font_scale=0.6, color=(0, 255, 0), bg_color=(0, 0, 0)
                )
                y_offset += 25
            
            # Mostrar
            cv2.imshow("Eulerian Magnification Demo", combined)
            
            # Manejar teclas
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('s'):
                cv2.imwrite(f"snapshot_{frame_count}.png", combined)
                print(f"Snapshot guardado: snapshot_{frame_count}.png")
            elif key == ord('1'):
                # Preset pulso
                processor.set_amplification(50)
                processor.set_frequency_range(0.4, 3.0)
                print("Preset: Detección de pulso")
            elif key == ord('2'):
                # Preset movimiento
                processor.set_amplification(20)
                processor.set_frequency_range(0.05, 0.4)
                print("Preset: Amplificación de movimiento")
            elif key == ord('3'):
                # Preset respiración
                processor.set_amplification(100)
                processor.set_frequency_range(0.2, 0.5)
                print("Preset: Detección de respiración")
            elif key == ord('+') or key == ord('='):
                new_amp = min(processor.amplification_factor + 10, 200)
                processor.set_amplification(new_amp)
                print(f"Amplificación: {new_amp}")
            elif key == ord('-') or key == ord('_'):
                new_amp = max(processor.amplification_factor - 10, 10)
                processor.set_amplification(new_amp)
                print(f"Amplificación: {new_amp}")
    
    except KeyboardInterrupt:
        print("\nInterrumpido")
    
    finally:
        # Limpiar
        camera.stop()
        processor.stop()
        display.stop()
        
        camera.cleanup()
        processor.cleanup()
        display.cleanup()
        
        cv2.destroyAllWindows()
        
        # Estadísticas
        stats = fps_counter.get_stats()
        print("\n" + "=" * 60)
        print("ESTADÍSTICAS")
        print("=" * 60)
        print(f"Frames procesados: {frame_count}")
        print(f"FPS promedio: {stats['average_fps']:.2f}")
        print(f"Tiempo total: {stats['elapsed_time']:.2f}s")
        print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
