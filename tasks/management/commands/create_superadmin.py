from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from tasks.models import Usuarios

class Command(BaseCommand):
    help = 'Crea un superadmin por defecto'

    def handle(self, *args, **kwargs): # Definir el método handle que se ejecutará cuando se invoque el comando
        if not Usuarios.objects.filter(cedula='0000000000').exists():  # Verificar si no existe un usuario con la cédula '0000000000'
            # Crear un nuevo usuario con la cédula '0000000000' y otros datos por defecto
            Usuarios.objects.create(
                cedula='0000000000',
                nombre_persona='Admin Super',
                nombre_usuario='superadmin',
                contraseña=make_password('12345678'), 
                rol='superadmin'
            )
            self.stdout.write(self.style.SUCCESS('Superadmin creado con éxito')) # Mostrar un mensaje de éxito en la consola
        else:
            self.stdout.write(self.style.WARNING('El superadmin ya existe')) # Mostrar un mensaje de advertencia en la consola si el superadministrador ya existe