from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from tasks.models import Usuarios

class Command(BaseCommand):
    help = 'Crea un superadmin por defecto'

    def handle(self, *args, **kwargs):
        if not Usuarios.objects.filter(cedula='0000000000').exists():
            Usuarios.objects.create(
                cedula='0000000000',
                nombre_persona='Admin Super',
                nombre_usuario='superadmin',
                contraseña=make_password('12345678'),
                rol='superadmin'
            )
            self.stdout.write(self.style.SUCCESS('Superadmin creado con éxito'))
        else:
            self.stdout.write(self.style.WARNING('El superadmin ya existe'))