#!/usr/bin/env python3
"""
module_manager.py - CLI para gestionar módulos de dispositivos.
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.module_loader import ModuleLoader
from core.config_manager import ConfigManager
from utils.logger import setup_logger


def parse_arguments():
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Gestor de módulos de dispositivos PureVision"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    
    # List
    subparsers.add_parser("list", help="Lista módulos disponibles")
    
    # Info
    info_parser = subparsers.add_parser("info", help="Información de un módulo")
    info_parser.add_argument("module", help="Nombre del módulo")
    
    # Validate
    validate_parser = subparsers.add_parser("validate", help="Valida un módulo")
    validate_parser.add_argument("module", help="Nombre del módulo")
    
    # Enable/Disable
    enable_parser = subparsers.add_parser("enable", help="Habilita un dispositivo")
    enable_parser.add_argument("device", help="Nombre del dispositivo")
    
    disable_parser = subparsers.add_parser("disable", help="Deshabilita un dispositivo")
    disable_parser.add_argument("device", help="Nombre del dispositivo")
    
    return parser.parse_args()


def cmd_list(module_loader):
    """Lista módulos disponibles."""
    print("\n📦 MÓDULOS DISPONIBLES:\n")
    
    modules = module_loader.discover_modules()
    loaded = module_loader.get_loaded_modules()
    
    for module in modules:
        status = "✓ Cargado" if module in loaded else "○ No cargado"
        print(f"  {status}  {module}")
    
    print(f"\nTotal: {len(modules)} módulos\n")


def cmd_info(module_loader, module_name):
    """Muestra información de un módulo."""
    print(f"\n📋 INFORMACIÓN DEL MÓDULO: {module_name}\n")
    
    device_class = module_loader.load_module(module_name)
    
    if not device_class:
        print("  ✗ No se pudo cargar el módulo\n")
        return
    
    print(f"  Clase: {device_class.__name__}")
    print(f"  Archivo: {module_name}.py")
    
    if device_class.__doc__:
        print(f"\n  Descripción:")
        for line in device_class.__doc__.strip().split('\n'):
            print(f"    {line}")
    
    # Métodos
    print(f"\n  Métodos implementados:")
    methods = ["initialize", "start", "stop", "process", "cleanup", "get_info"]
    for method in methods:
        has_method = "✓" if hasattr(device_class, method) else "✗"
        print(f"    {has_method} {method}")
    
    print()


def cmd_validate(module_loader, module_name):
    """Valida un módulo."""
    print(f"\n🔍 VALIDANDO MÓDULO: {module_name}\n")
    
    if module_loader.validate_module(module_name):
        print("  ✓ Módulo válido\n")
    else:
        print("  ✗ Módulo inválido\n")


def cmd_enable(config_manager, device_name):
    """Habilita un dispositivo en la configuración."""
    devices_config = config_manager.get_config("devices")
    
    if not devices_config:
        print("  ✗ No se pudo cargar configuración de dispositivos\n")
        return
    
    if device_name not in devices_config.get("devices", {}):
        print(f"  ✗ Dispositivo '{device_name}' no encontrado\n")
        return
    
    devices_config["devices"][device_name]["enabled"] = True
    
    if config_manager.save_config("devices"):
        print(f"  ✓ Dispositivo '{device_name}' habilitado\n")
    else:
        print(f"  ✗ Error al guardar configuración\n")


def cmd_disable(config_manager, device_name):
    """Deshabilita un dispositivo en la configuración."""
    devices_config = config_manager.get_config("devices")
    
    if not devices_config:
        print("  ✗ No se pudo cargar configuración de dispositivos\n")
        return
    
    if device_name not in devices_config.get("devices", {}):
        print(f"  ✗ Dispositivo '{device_name}' no encontrado\n")
        return
    
    devices_config["devices"][device_name]["enabled"] = False
    
    if config_manager.save_config("devices"):
        print(f"  ✓ Dispositivo '{device_name}' deshabilitado\n")
    else:
        print(f"  ✗ Error al guardar configuración\n")


def main():
    """Función principal."""
    args = parse_arguments()
    
    logger = setup_logger("ModuleManager", log_to_file=False)
    
    # Inicializar componentes
    module_loader = ModuleLoader("src/modules")
    config_manager = ConfigManager("config")
    
    if not args.command:
        print("Error: Debe especificar un comando. Use --help para ver opciones.")
        return 1
    
    # Ejecutar comando
    if args.command == "list":
        cmd_list(module_loader)
    
    elif args.command == "info":
        cmd_info(module_loader, args.module)
    
    elif args.command == "validate":
        cmd_validate(module_loader, args.module)
    
    elif args.command == "enable":
        cmd_enable(config_manager, args.device)
    
    elif args.command == "disable":
        cmd_disable(config_manager, args.device)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
