from django.db import models
from django.utils import timezone

class Usuarios(models.Model):
    cedula = models.CharField(max_length=10, primary_key=True)  # Identificador único del usuario
    nombre_persona = models.CharField(max_length=50)  # Nombre completo de la persona
    nombre_usuario = models.CharField(max_length=50, unique=True)  # Nombre de usuario único
    contraseña = models.CharField(max_length=100)  # Contraseña del usuario
    rol = models.CharField(max_length=20)  # Rol del usuario en el sistema

    def __str__(self):
        return self.nombre_usuario

    class Meta:
        db_table = 'usuarios'  # Nombre de la tabla en la base de datos

class Proyectos(models.Model):
    OT = 'OT'  # Código para tipo de proyecto 'Orden de Trabajo'
    OI = 'OI'  # Código para tipo de proyecto 'Orden de Ingeniería'
    TIPO_PROYECTO_CHOICES = [
        (OT, 'OT'),
        (OI, 'OI'),
    ]

    proyecto = models.CharField(max_length=40, primary_key=True)  # Combinación de numero y tipo_proyecto
    tipo_proyecto = models.CharField(max_length=2, choices=TIPO_PROYECTO_CHOICES)  # Tipo de proyecto
    numero = models.CharField(max_length=10)  # Número del proyecto

    def save(self, *args, **kwargs):
        self.proyecto = f"{self.tipo_proyecto}-{self.numero}"  # Generar el identificador del proyecto
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('tipo_proyecto', 'numero')  # Restricción de unicidad en combinación de tipo_proyecto y numero
        db_table = 'proyectos'  # Nombre de la tabla en la base de datos

    def __str__(self):
        return f"{self.proyecto}"
        
class Tableros(models.Model):
    identificador = models.CharField(max_length=50, primary_key=True)  # Identificador único del tablero
    item = models.IntegerField()  # El item será ingresado manualmente
    proyecto = models.ForeignKey('Proyectos', on_delete=models.CASCADE)  # Proyecto asociado al tablero

    def save(self, *args, **kwargs):
        if not self.identificador:
            # Crear el identificador basado en el proyecto y el item
            self.identificador = f"{self.proyecto.tipo_proyecto}-{self.proyecto.numero}-{self.item}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.identificador}"

    class Meta:
        db_table = 'tableros'
        unique_together = ('proyecto', 'item')  # Asegurar que el item sea único por proyecto

class Cables(models.Model):
    referencia = models.IntegerField(primary_key=True)
    descripcion = models.CharField(max_length=200)
    cantidad_inicial = models.IntegerField()
    cantidad_restante = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=1)
    ultima_advertencia = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.cantidad_restante = self.cantidad_inicial
        super().save(*args, **kwargs)

    def actualizar_cantidad_restante(self, cantidad_dispensada):
        if cantidad_dispensada > self.cantidad_restante:
            raise ValueError("La cantidad dispensada no puede ser mayor que la cantidad restante.")
        self.cantidad_restante -= cantidad_dispensada
        self.save()

    def verificar_stock_minimo(self):
        return self.cantidad_restante < self.stock_minimo

    def necesita_advertencia(self):
        if self.verificar_stock_minimo():
            if self.ultima_advertencia is None or timezone.now() - self.ultima_advertencia > timezone.timedelta(days=1):
                return True
        return False

    def __str__(self):
        return f"{self.referencia} - {self.descripcion} - Cantidad Restante: {self.cantidad_restante}"

    class Meta:
        db_table = 'cables'