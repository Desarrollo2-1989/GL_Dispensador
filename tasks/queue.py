# dispensador/queue.py

from collections import deque
from django.core.cache import cache

class DispenserQueue:
    def __init__(self):
        self.queue_key = 'dispenser_queue'
        self.active_request_key = 'active_dispenser_request'
    
    def get_queue(self):
        """Obtener la cola actual del caché."""
        return cache.get(self.queue_key, deque())
    
    def save_queue(self, queue):
        """Guardar la cola en el caché."""
        cache.set(self.queue_key, queue)
    
    def add_request(self, request_data):
        """Añadir una nueva solicitud a la cola."""
        queue = self.get_queue()
        queue.append(request_data)
        self.save_queue(queue)
    
    def get_active_request(self):
        """Obtener la solicitud activa actual."""
        return cache.get(self.active_request_key)
    
    def set_active_request(self, request_data):
        """Establecer la solicitud activa."""
        cache.set(self.active_request_key, request_data)
    
    def remove_active_request(self):
        """Eliminar la solicitud activa."""
        cache.delete(self.active_request_key)
    
    def process_next(self):
        """Procesar la siguiente solicitud en la cola."""
        queue = self.get_queue()
        if queue and not self.get_active_request():
            next_request = queue.popleft()
            self.save_queue(queue)
            self.set_active_request(next_request)
            return next_request
        return None

# Inicializar la cola
dispenser_queue = DispenserQueue()