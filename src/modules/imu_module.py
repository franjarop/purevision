"""
IMUModule - Módulo ejemplo para sensores IMU (acelerómetro, giroscopio).
Este es un módulo de ejemplo para mostrar cómo integrar sensores adicionales.
"""

import numpy as np
from typing import Any, Dict, Optional, Tuple
import logging

import sys
sys.path.append('src')

from core.base_device import BaseDevice, DeviceStatus


class IMUModule(BaseDevice):
    """
    Módulo ejemplo para sensores IMU (Inertial Measurement Unit).
    
    Este módulo sirve como ejemplo de cómo integrar nuevos dispositivos.
    Puede adaptarse para sensores reales como MPU6050, BNO055, etc.
    
    Proporciona:
    - Lecturas de acelerómetro (x, y, z)
    - Lecturas de giroscopio (x, y, z)
    - Cálculo de orientación
    """
    
    def __init__(self, device_id: str, config: Dict[str, Any]):
        """
        Inicializa el módulo IMU.
        
        Args:
            device_id: Identificador único del sensor
            config: Configuración con:
                - sensor_type: Tipo de sensor ('mpu6050', 'bno055', etc.)
                - i2c_bus: Bus I2C (por defecto 1)
                - i2c_address: Dirección I2C del sensor
                - sample_rate: Tasa de muestreo (Hz)
                - simulation_mode: Usar datos simulados para pruebas
        """
        super().__init__(device_id, config)
        
        self.sensor_type = config.get("sensor_type", "mpu6050")
        self.i2c_bus = config.get("i2c_bus", 1)
        self.i2c_address = config.get("i2c_address", 0x68)
        self.sample_rate = config.get("sample_rate", 100)
        self.simulation_mode = config.get("simulation_mode", True)
        
        self.sensor = None
        self.reading_count = 0
        
        # Últimas lecturas
        self.last_accel = np.zeros(3)
        self.last_gyro = np.zeros(3)
        self.last_orientation = np.zeros(3)
    
    def initialize(self) -> bool:
        """
        Inicializa el sensor IMU.
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            self.logger.info(f"Inicializando sensor IMU: {self.sensor_type}")
            
            if self.simulation_mode:
                self.logger.info("Modo simulación activado")
                return True
            
            # Aquí iría la inicialización real del sensor
            # Por ejemplo, para MPU6050:
            # from mpu6050 import mpu6050
            # self.sensor = mpu6050(self.i2c_address)
            
            self.logger.warning("Sensor real no implementado, usando simulación")
            self.simulation_mode = True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al inicializar IMU: {e}")
            return False
    
    def start(self) -> bool:
        """
        Inicia la lectura del sensor.
        
        Returns:
            True si se inició correctamente
        """
        self.logger.info("Sensor IMU iniciado")
        return True
    
    def stop(self) -> bool:
        """
        Detiene la lectura del sensor.
        
        Returns:
            True si se detuvo correctamente
        """
        self.logger.info("Sensor IMU detenido")
        return True
    
    def process(self, data: Optional[Any] = None) -> Dict[str, Any]:
        """
        Lee datos del sensor IMU.
        
        Args:
            data: No utilizado
            
        Returns:
            Diccionario con lecturas del sensor
        """
        try:
            if self.simulation_mode:
                # Generar datos simulados
                accel = self._simulate_accelerometer()
                gyro = self._simulate_gyroscope()
            else:
                # Leer del sensor real
                accel = self._read_accelerometer()
                gyro = self._read_gyroscope()
            
            # Actualizar últimas lecturas
            self.last_accel = accel
            self.last_gyro = gyro
            self.reading_count += 1
            
            # Calcular orientación (simplificado)
            orientation = self._calculate_orientation(accel, gyro)
            self.last_orientation = orientation
            
            return {
                "accelerometer": {
                    "x": float(accel[0]),
                    "y": float(accel[1]),
                    "z": float(accel[2])
                },
                "gyroscope": {
                    "x": float(gyro[0]),
                    "y": float(gyro[1]),
                    "z": float(gyro[2])
                },
                "orientation": {
                    "roll": float(orientation[0]),
                    "pitch": float(orientation[1]),
                    "yaw": float(orientation[2])
                },
                "timestamp": self.reading_count
            }
            
        except Exception as e:
            self.logger.error(f"Error al leer sensor IMU: {e}")
            return {}
    
    def cleanup(self) -> None:
        """
        Libera recursos del sensor.
        """
        if self.sensor:
            # Aquí iría la limpieza del sensor real
            pass
        
        self.logger.info("Recursos de IMU liberados")
    
    def get_info(self) -> Dict[str, Any]:
        """
        Retorna información del sensor IMU.
        
        Returns:
            Diccionario con información del dispositivo
        """
        return {
            "type": "imu",
            "sensor_type": self.sensor_type,
            "i2c_bus": self.i2c_bus,
            "i2c_address": hex(self.i2c_address),
            "sample_rate": self.sample_rate,
            "simulation_mode": self.simulation_mode,
            "readings_count": self.reading_count,
            "last_accel": self.last_accel.tolist(),
            "last_gyro": self.last_gyro.tolist()
        }
    
    def _simulate_accelerometer(self) -> np.ndarray:
        """
        Simula lecturas de acelerómetro.
        
        Returns:
            Array con valores [x, y, z] en g
        """
        # Simular gravedad con algo de ruido
        base = np.array([0.0, 0.0, 1.0])  # Gravedad en eje Z
        noise = np.random.normal(0, 0.05, 3)
        return base + noise
    
    def _simulate_gyroscope(self) -> np.ndarray:
        """
        Simula lecturas de giroscopio.
        
        Returns:
            Array con valores [x, y, z] en grados/segundo
        """
        # Simular pequeñas rotaciones
        return np.random.normal(0, 1.0, 3)
    
    def _read_accelerometer(self) -> np.ndarray:
        """
        Lee el acelerómetro real.
        
        Returns:
            Array con valores [x, y, z] en g
        """
        if self.sensor:
            # Aquí iría la lectura real, por ejemplo:
            # accel_data = self.sensor.get_accel_data()
            # return np.array([accel_data['x'], accel_data['y'], accel_data['z']])
            pass
        
        return self._simulate_accelerometer()
    
    def _read_gyroscope(self) -> np.ndarray:
        """
        Lee el giroscopio real.
        
        Returns:
            Array con valores [x, y, z] en grados/segundo
        """
        if self.sensor:
            # Aquí iría la lectura real, por ejemplo:
            # gyro_data = self.sensor.get_gyro_data()
            # return np.array([gyro_data['x'], gyro_data['y'], gyro_data['z']])
            pass
        
        return self._simulate_gyroscope()
    
    def _calculate_orientation(self, accel: np.ndarray, gyro: np.ndarray) -> np.ndarray:
        """
        Calcula orientación a partir de accel y gyro (método simplificado).
        
        Args:
            accel: Valores del acelerómetro
            gyro: Valores del giroscopio
            
        Returns:
            Array con [roll, pitch, yaw] en grados
        """
        # Cálculo simplificado usando solo acelerómetro
        # En implementación real usar filtro complementario o Kalman
        
        roll = np.arctan2(accel[1], accel[2]) * 180 / np.pi
        pitch = np.arctan2(-accel[0], np.sqrt(accel[1]**2 + accel[2]**2)) * 180 / np.pi
        yaw = 0  # No se puede calcular yaw solo con acelerómetro
        
        return np.array([roll, pitch, yaw])
    
    def calibrate(self) -> bool:
        """
        Calibra el sensor IMU.
        
        Returns:
            True si la calibración fue exitosa
        """
        self.logger.info("Iniciando calibración del IMU...")
        
        # Recolectar muestras en reposo
        samples = []
        for _ in range(100):
            accel = self._read_accelerometer()
            samples.append(accel)
        
        # Calcular offset
        offset = np.mean(samples, axis=0)
        self.logger.info(f"Calibración completada. Offset: {offset}")
        
        return True
