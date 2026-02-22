#!/usr/bin/env python3
"""
device_list.py - Lista dispositivos detectados en el sistema.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.device_detector import DeviceDetector
from utils.logger import setup_logger
import json


def main():
    """Función principal."""
    logger = setup_logger("DeviceList", log_to_file=False)
    
    logger.info("Detectando dispositivos en el sistema...")
    
    detector = DeviceDetector()
    devices = detector.detect_all()
    
    # Mostrar resultados
    print("\n" + "=" * 60)
    print("DISPOSITIVOS DETECTADOS")
    print("=" * 60)
    
    # Sistema
    print("\n📱 INFORMACIÓN DEL SISTEMA:")
    for key, value in devices["system_info"].items():
        print(f"  {key}: {value}")
    
    # Cámaras
    print("\n📷 CÁMARAS:")
    if devices["cameras"]:
        for i, camera in enumerate(devices["cameras"], 1):
            print(f"\n  Cámara #{i}:")
            for key, value in camera.items():
                print(f"    {key}: {value}")
    else:
        print("  No se detectaron cámaras")
    
    # USB
    print("\n🔌 DISPOSITIVOS USB:")
    if devices["usb_devices"]:
        for i, device in enumerate(devices["usb_devices"][:10], 1):
            print(f"  {i}. {device.get('info', 'N/A')}")
        if len(devices["usb_devices"]) > 10:
            print(f"  ... y {len(devices['usb_devices']) - 10} más")
    else:
        print("  No se detectaron dispositivos USB")
    
    # I2C
    print("\n🔗 DISPOSITIVOS I2C:")
    if devices["i2c_devices"]:
        for bus_info in devices["i2c_devices"]:
            print(f"\n  Bus I2C #{bus_info['bus']}:")
            print(f"    Direcciones: {', '.join(['0x' + addr for addr in bus_info['addresses']])}")
    else:
        print("  No se detectaron dispositivos I2C")
    
    # GPIO
    print("\n⚡ GPIO:")
    if devices["gpio_available"]:
        print("  ✓ GPIO disponible")
    else:
        print("  ✗ GPIO no disponible")
    
    print("\n" + "=" * 60)
    
    # Opción de guardar a JSON
    print("\n¿Guardar resultados a JSON? (s/n): ", end="")
    try:
        response = input().lower()
        if response == 's':
            output_file = Path("detected_devices.json")
            with open(output_file, 'w') as f:
                json.dump(devices, f, indent=2)
            print(f"✓ Resultados guardados en: {output_file}")
    except (EOFError, KeyboardInterrupt):
        print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
