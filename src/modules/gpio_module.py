"""
GPIOModule - Módulo para control de GPIO en Jetson Nano.
Permite controlar pines GPIO para LEDs, botones, sensores, etc.
"""

from typing import Any, Dict, Optional
import logging

import sys
sys.path.append('src')

from core.base_device import BaseDevice, DeviceStatus

# Intentar importar Jetson.GPIO
try:
    import Jetson.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    import warnings
    warnings.warn("Jetson.GPIO no disponible. Modo simulación activado.")


class GPIOModule(BaseDevice):
    """
    Módulo de control GPIO para Jetson Nano Orin.
    
    Permite:
    - Configurar pines como entrada/salida
    - Leer estados de pines
    - Escribir valores a pines
    - Configurar pull-up/pull-down
    - Detectar eventos en pines
    """
    
    # Modos de numeración
    BOARD = "BOARD"  # Numeración física del pin
    BCM = "BCM"      # Numeración BCM
    
    # Direcciones
    IN = "IN"
    OUT = "OUT"
    
    # Valores
    HIGH = True
    LOW = False
    
    def __init__(self, device_id: str, config: Dict[str, Any]):
        """
        Inicializa el módulo GPIO.
        
        Args:
            device_id: Identificador único del módulo
            config: Configuración con:
                - mode: 'BOARD' o 'BCM' (modo de numeración)
                - pins: Dict con configuración de pines
                  Ejemplo: {7: {'direction': 'OUT', 'initial': False}}
        """
        super().__init__(device_id, config)
        
        self.mode = config.get("mode", "BOARD")
        self.pins_config = config.get("pins", {})
        self.configured_pins = {}
        
        self.gpio_available = GPIO_AVAILABLE
    
    def initialize(self) -> bool:
        """
        Inicializa el sistema GPIO.
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            if not self.gpio_available:
                self.logger.warning("GPIO no disponible, modo simulación")
                return True
            
            self.logger.info(f"Inicializando GPIO en modo {self.mode}")
            
            # Configurar modo de numeración
            if self.mode == "BOARD":
                GPIO.setmode(GPIO.BOARD)
            else:
                GPIO.setmode(GPIO.BCM)
            
            # Configurar warnings
            GPIO.setwarnings(False)
            
            # Configurar pines definidos en config
            for pin, pin_config in self.pins_config.items():
                self._setup_pin(int(pin), pin_config)
            
            self.logger.info(f"GPIO inicializado con {len(self.configured_pins)} pines")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al inicializar GPIO: {e}")
            return False
    
    def start(self) -> bool:
        """
        Inicia el módulo GPIO.
        
        Returns:
            True si se inició correctamente
        """
        self.logger.info("Módulo GPIO iniciado")
        return True
    
    def stop(self) -> bool:
        """
        Detiene el módulo GPIO.
        
        Returns:
            True si se detuvo correctamente
        """
        self.logger.info("Módulo GPIO detenido")
        return True
    
    def process(self, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Procesa comandos GPIO.
        
        Args:
            data: Diccionario con comandos:
                - action: 'read', 'write', 'toggle'
                - pin: Número de pin
                - value: Valor (para write)
            
        Returns:
            Resultado de la operación
        """
        if data is None:
            return None
        
        action = data.get("action")
        pin = data.get("pin")
        
        if action == "read":
            return {"pin": pin, "value": self.read_pin(pin)}
        elif action == "write":
            value = data.get("value", False)
            self.write_pin(pin, value)
            return {"pin": pin, "value": value, "success": True}
        elif action == "toggle":
            new_value = self.toggle_pin(pin)
            return {"pin": pin, "value": new_value, "success": True}
        else:
            self.logger.warning(f"Acción desconocida: {action}")
            return None
    
    def cleanup(self) -> None:
        """
        Libera recursos GPIO.
        """
        if self.gpio_available:
            GPIO.cleanup()
            self.logger.info("GPIO limpiado")
    
    def get_info(self) -> Dict[str, Any]:
        """
        Retorna información del módulo GPIO.
        
        Returns:
            Diccionario con información del dispositivo
        """
        return {
            "type": "gpio",
            "mode": self.mode,
            "gpio_available": self.gpio_available,
            "configured_pins": list(self.configured_pins.keys()),
            "pin_count": len(self.configured_pins)
        }
    
    def _setup_pin(self, pin: int, pin_config: Dict[str, Any]) -> bool:
        """
        Configura un pin específico.
        
        Args:
            pin: Número de pin
            pin_config: Configuración del pin
            
        Returns:
            True si se configuró correctamente
        """
        try:
            direction = pin_config.get("direction", "OUT")
            initial = pin_config.get("initial", False)
            pull_up_down = pin_config.get("pull_up_down", None)
            
            if not self.gpio_available:
                self.configured_pins[pin] = {
                    "direction": direction,
                    "value": initial
                }
                return True
            
            # Configurar según dirección
            if direction == "OUT":
                GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH if initial else GPIO.LOW)
            else:
                pud = GPIO.PUD_OFF
                if pull_up_down == "up":
                    pud = GPIO.PUD_UP
                elif pull_up_down == "down":
                    pud = GPIO.PUD_DOWN
                
                GPIO.setup(pin, GPIO.IN, pull_up_down=pud)
            
            self.configured_pins[pin] = {
                "direction": direction,
                "initial": initial,
                "pull_up_down": pull_up_down
            }
            
            self.logger.debug(f"Pin {pin} configurado como {direction}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al configurar pin {pin}: {e}")
            return False
    
    def setup_pin(self, pin: int, direction: str, initial: bool = False) -> bool:
        """
        Configura un pin dinámicamente.
        
        Args:
            pin: Número de pin
            direction: 'IN' o 'OUT'
            initial: Valor inicial (para OUT)
            
        Returns:
            True si se configuró correctamente
        """
        pin_config = {
            "direction": direction,
            "initial": initial
        }
        return self._setup_pin(pin, pin_config)
    
    def read_pin(self, pin: int) -> bool:
        """
        Lee el valor de un pin.
        
        Args:
            pin: Número de pin
            
        Returns:
            Estado del pin (True=HIGH, False=LOW)
        """
        if not self.gpio_available:
            return self.configured_pins.get(pin, {}).get("value", False)
        
        try:
            value = GPIO.input(pin)
            return bool(value)
        except Exception as e:
            self.logger.error(f"Error al leer pin {pin}: {e}")
            return False
    
    def write_pin(self, pin: int, value: bool) -> bool:
        """
        Escribe un valor a un pin.
        
        Args:
            pin: Número de pin
            value: Valor a escribir (True=HIGH, False=LOW)
            
        Returns:
            True si se escribió correctamente
        """
        if not self.gpio_available:
            if pin in self.configured_pins:
                self.configured_pins[pin]["value"] = value
            return True
        
        try:
            GPIO.output(pin, GPIO.HIGH if value else GPIO.LOW)
            return True
        except Exception as e:
            self.logger.error(f"Error al escribir pin {pin}: {e}")
            return False
    
    def toggle_pin(self, pin: int) -> bool:
        """
        Cambia el estado de un pin (HIGH<->LOW).
        
        Args:
            pin: Número de pin
            
        Returns:
            Nuevo valor del pin
        """
        current = self.read_pin(pin)
        new_value = not current
        self.write_pin(pin, new_value)
        return new_value
