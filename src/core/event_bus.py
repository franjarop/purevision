"""
EventBus - Sistema de eventos para comunicación entre módulos.
Implementa un patrón Publisher-Subscriber para desacoplar componentes.
"""

import logging
from typing import Any, Callable, Dict, List
from collections import defaultdict
import threading


class EventBus:
    """
    Bus de eventos para comunicación desacoplada entre módulos.
    
    Permite que los módulos publiquen eventos y se suscriban a eventos
    sin necesidad de conocerse directamente entre sí.
    """
    
    def __init__(self):
        """Inicializa el bus de eventos."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()
        
        self.logger.info("EventBus inicializado")
    
    def subscribe(self, event_name: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Suscribe un callback a un evento específico.
        
        Args:
            event_name: Nombre del evento al que suscribirse
            callback: Función a ejecutar cuando ocurra el evento
                     Debe aceptar un diccionario con los datos del evento
        """
        with self._lock:
            self._subscribers[event_name].append(callback)
            self.logger.debug(f"Suscriptor añadido al evento '{event_name}' "
                            f"({len(self._subscribers[event_name])} total)")
    
    def unsubscribe(self, event_name: str, callback: Callable) -> bool:
        """
        Cancela la suscripción de un callback a un evento.
        
        Args:
            event_name: Nombre del evento
            callback: Función a desuscribir
            
        Returns:
            True si se desuscribió correctamente, False si no estaba suscrito
        """
        with self._lock:
            if event_name in self._subscribers:
                try:
                    self._subscribers[event_name].remove(callback)
                    self.logger.debug(f"Suscriptor eliminado del evento '{event_name}'")
                    
                    # Limpiar lista vacía
                    if not self._subscribers[event_name]:
                        del self._subscribers[event_name]
                    
                    return True
                except ValueError:
                    self.logger.warning(f"Callback no encontrado en evento '{event_name}'")
                    return False
            return False
    
    def publish(self, event_name: str, data: Dict[str, Any] = None) -> None:
        """
        Publica un evento a todos los suscriptores.
        
        Args:
            event_name: Nombre del evento a publicar
            data: Datos asociados al evento (opcional)
        """
        with self._lock:
            subscribers = self._subscribers.get(event_name, []).copy()
        
        if not subscribers:
            self.logger.debug(f"Evento '{event_name}' publicado sin suscriptores")
            return
        
        event_data = data or {}
        self.logger.debug(f"Publicando evento '{event_name}' a {len(subscribers)} suscriptores")
        
        # Ejecutar callbacks fuera del lock para evitar deadlocks
        for callback in subscribers:
            try:
                callback(event_data)
            except Exception as e:
                self.logger.error(f"Error en callback de '{event_name}': {e}", exc_info=True)
    
    def publish_async(self, event_name: str, data: Dict[str, Any] = None) -> None:
        """
        Publica un evento de forma asíncrona (en un thread separado).
        
        Args:
            event_name: Nombre del evento a publicar
            data: Datos asociados al evento (opcional)
        """
        thread = threading.Thread(
            target=self.publish,
            args=(event_name, data),
            name=f"EventBus-{event_name}"
        )
        thread.daemon = True
        thread.start()
    
    def clear_event(self, event_name: str) -> None:
        """
        Elimina todos los suscriptores de un evento específico.
        
        Args:
            event_name: Nombre del evento a limpiar
        """
        with self._lock:
            if event_name in self._subscribers:
                count = len(self._subscribers[event_name])
                del self._subscribers[event_name]
                self.logger.info(f"Eliminados {count} suscriptores del evento '{event_name}'")
    
    def clear_all(self) -> None:
        """Elimina todos los suscriptores de todos los eventos."""
        with self._lock:
            total_events = len(self._subscribers)
            total_subscribers = sum(len(subs) for subs in self._subscribers.values())
            self._subscribers.clear()
            self.logger.info(f"Eliminados {total_subscribers} suscriptores "
                           f"de {total_events} eventos")
    
    def get_events(self) -> List[str]:
        """
        Obtiene la lista de eventos con suscriptores activos.
        
        Returns:
            Lista de nombres de eventos
        """
        with self._lock:
            return list(self._subscribers.keys())
    
    def get_subscriber_count(self, event_name: str) -> int:
        """
        Obtiene el número de suscriptores de un evento.
        
        Args:
            event_name: Nombre del evento
            
        Returns:
            Número de suscriptores
        """
        with self._lock:
            return len(self._subscribers.get(event_name, []))
    
    def __repr__(self) -> str:
        return (f"EventBus(events={len(self._subscribers)}, "
                f"subscribers={sum(len(s) for s in self._subscribers.values())})")
