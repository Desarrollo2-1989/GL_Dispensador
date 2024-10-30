from django.db import models
from django.utils import timezone

class Usuarios(models.Model):
    cedula = models.CharField(max_length=20, primary_key=True)  # Identificador único del usuario
    nombre_persona = models.CharField(max_length=50)  # Nombre completo de la persona
    nombre_usuario = models.CharField(max_length=50, unique=True)  # Nombre de usuario único
    contraseña = models.CharField(max_length=100)  # Contraseña del usuario
    rol = models.CharField(max_length=20)  # Rol del usuario en el sistema
    estado = models.BooleanField(default=True)  # Estado del usuario (True = Activo, False = Inactivo)

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
    referencia = models.IntegerField(primary_key=True)  # Clave primaria
    descripcion = models.CharField(max_length=200)  # Descripción del cable
    cantidad_inicial = models.IntegerField()  # Cantidad inicial del cable
    cantidad_restante = models.IntegerField(default=0)  # Cantidad restante del cable
    stock_minimo = models.IntegerField(default=1)  # Stock mínimo del cable
    ultima_advertencia = models.DateTimeField(null=True, blank=True)  # Fecha de la última advertencia

    # Métodos
    def save(self, *args, **kwargs):  # Método para guardar el objeto
        if self.pk is None:
            self.cantidad_restante = self.cantidad_inicial
        super().save(*args, **kwargs)

    def actualizar_cantidad_restante(self, cantidad_dispensada):  # Método para actualizar la cantidad restante
        if cantidad_dispensada > self.cantidad_restante:
            raise ValueError("La cantidad dispensada no puede ser mayor que la cantidad restante.")
        self.cantidad_restante -= cantidad_dispensada
        self.save()

    def verificar_stock_minimo(self):  # Método para verificar el stock mínimo
        return self.cantidad_restante < self.stock_minimo

    def necesita_advertencia(self):  # Método para verificar si se necesita una advertencia
        if self.verificar_stock_minimo():
            if self.ultima_advertencia is None or timezone.now() - self.ultima_advertencia > timezone.timedelta(days=1):
                return True
        return False

    def __str__(self):  # Método para representar el objeto como string
        return f"{self.referencia} - {self.descripcion} - Cantidad Restante: {self.cantidad_restante}"

    class Meta:
        db_table = 'cables'  # Nombre de la tabla en la base de datos
        
class MensajePruebaDP(models.Model):
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mensaje Prueba-DP recibido el {self.fecha}: {self.mensaje}"
    
    class Meta:
        db_table = 'topic1'  # Nombre de la tabla en la base de datos
        

class RegistroDispensa(models.Model):
    cable = models.ForeignKey(Cables, on_delete=models.CASCADE)  # Relación con el modelo de Cables
    cantidad_dispensada = models.FloatField()  # Cantidad de cable dispensada
    fecha = models.DateTimeField(auto_now_add=True)  # Fecha de la dispensación
    proyecto = models.ForeignKey(Proyectos, on_delete=models.CASCADE)  # Relación con el modelo Proyectos
    tablero = models.ForeignKey(Tableros, on_delete=models.CASCADE)  # Relación con el modelo Tableros
    cantidad_restante_despues = models.IntegerField(default=0)
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, null=True)
    

    def __str__(self):
        return f"{self.cantidad_dispensada} metros de cable dispensados el {self.fecha} para el proyecto {self.proyecto} en el tablero {self.tablero}"

    class Meta:
        db_table = 'registro_dispensas'  # Nombre de la tabla en la base de datos
        
             
class DestinatarioCorreo(models.Model):
    correo = models.EmailField(unique=True)

    def __str__(self):
        return self.correo
    

        
