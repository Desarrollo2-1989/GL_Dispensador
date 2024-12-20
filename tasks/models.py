from django.db import models  # Importa la clase models para definir los modelos de la base de datos
from django.utils import timezone  # Importa timezone para trabajar con fechas y horas de manera eficiente
from django.contrib.auth.models import User

# Modelo para representar usuarios en el sistema
class Usuarios(models.Model):
    cedula = models.CharField(max_length=20, primary_key=True)  # Identificador único del usuario, clave primaria
    nombre_persona = models.CharField(max_length=50)  # Nombre completo de la persona
    nombre_usuario = models.CharField(max_length=50, unique=True)  # Nombre de usuario único, no puede repetirse
    contraseña = models.CharField(max_length=100)  # Contraseña del usuario, almacenada como texto
    rol = models.CharField(max_length=20)  # Rol del usuario en el sistema (ej. administrador, operador, auditor)
    estado = models.BooleanField(default=True)  # Estado del usuario (True = Activo, False = Inactivo)

    def __str__(self):  # Método para representar el objeto como una cadena
        return self.nombre_usuario  # Devuelve el nombre de usuario como representación del objeto

    class Meta:  # Clase interna para definir metadatos del modelo
        db_table = 'usuarios'  # Nombre de la tabla en la base de datos

# Modelo para representar proyectos
class Proyectos(models.Model):
    OT = 'OT'  # Código para tipo de proyecto 'Orden de Trabajo'
    OI = 'OI'  # Código para tipo de proyecto 'Orden de Ingeniería'
    TIPO_PROYECTO_CHOICES = [  # Opciones disponibles para el tipo de proyecto
        (OT, 'OT'),  # Opción para Orden de Trabajo
        (OI, 'OI'),  # Opción para Orden de Ingeniería
    ]

    proyecto = models.CharField(max_length=40, primary_key=True)  # Combinación de numero y tipo_proyecto, clave primaria
    tipo_proyecto = models.CharField(max_length=2, choices=TIPO_PROYECTO_CHOICES)  # Tipo de proyecto seleccionado de las opciones
    numero = models.CharField(max_length=10)  # Número del proyecto, parte de la identificación del proyecto

    def save(self, *args, **kwargs):  # Método para guardar el objeto en la base de datos
        self.proyecto = f"{self.tipo_proyecto}-{self.numero}"  # Generar el identificador del proyecto a partir de tipo_proyecto y numero
        super().save(*args, **kwargs)  # Llama al método save de la clase base para completar la operación de guardado

    class Meta:  # Clase interna para definir metadatos del modelo
        unique_together = ('tipo_proyecto', 'numero')  # Restricción de unicidad en combinación de tipo_proyecto y numero
        db_table = 'proyectos'  # Nombre de la tabla en la base de datos

    def __str__(self):  # Método para representar el objeto como una cadena
        return f"{self.proyecto}"  # Devuelve el identificador del proyecto como representación del objeto

# Modelo para representar tableros asociados a proyectos
class Tableros(models.Model):
    identificador = models.CharField(max_length=50, primary_key=True)  # Identificador único del tablero
    item = models.IntegerField()  # El item será ingresado manualmente, representa un número o código asociado al tablero
    proyecto = models.ForeignKey('Proyectos', on_delete=models.CASCADE)  # Proyecto asociado al tablero, con relación de clave foránea

    def save(self, *args, **kwargs):  # Método para guardar el objeto en la base de datos
        if not self.identificador:  # Comprueba si no se ha establecido un identificador
            # Crear el identificador basado en el proyecto y el item
            # El formato será 'tipo_proyecto-número-item', donde 'tipo_proyecto' y 'número' provienen del proyecto asociado
            self.identificador = f"{self.proyecto.tipo_proyecto}-{self.proyecto.numero}-{self.item}"
        super().save(*args, **kwargs)  # Llama al método save de la clase base para completar la operación de guardado

    def __str__(self):  # Método para representar el objeto como una cadena
        return f"{self.identificador}"  # Devuelve el identificador del tablero como representación del objeto

    class Meta:  # Clase interna para definir metadatos del modelo
        db_table = 'tableros'  # Nombre de la tabla en la base de datos
        unique_together = ('proyecto', 'item')  # Asegurar que el item sea único por proyecto, evitando duplicados

# Modelo para representar los cables
class Cables(models.Model):
    referencia = models.IntegerField(primary_key=True)  # Clave primaria para identificar de forma única cada cable
    descripcion = models.CharField(max_length=200)  # Descripción del cable
    cantidad_inicial = models.IntegerField()  # Cantidad inicial del cable disponible
    cantidad_restante = models.IntegerField(default=0)  # Cantidad restante del cable después de dispensaciones
    stock_minimo = models.IntegerField(default=1)  # Nivel mínimo de stock que se debe mantener

    # Métodos
    def save(self, *args, **kwargs):  # Método para guardar el objeto en la base de datos
        if self.pk is None:  # Solo se ejecuta al crear un nuevo objeto
            self.cantidad_restante = self.cantidad_inicial  # Inicializa la cantidad restante con la cantidad inicial
        super().save(*args, **kwargs)  # Llama al método save de la clase base

    def actualizar_cantidad_restante(self, cantidad_dispensada):  # Método para actualizar la cantidad restante de cable
        if cantidad_dispensada > self.cantidad_restante:  # Verifica si la cantidad dispensada es mayor que la cantidad restante
            raise ValueError("La cantidad dispensada no puede ser mayor que la cantidad restante.")  # Lanza un error si es el caso
        self.cantidad_restante -= cantidad_dispensada  # Reduce la cantidad restante por la cantidad dispensada
        self.save()  # Guarda los cambios en la base de datos

    def verificar_stock_minimo(self):  # Método para verificar si la cantidad restante es inferior al stock mínimo
        return self.cantidad_restante < self.stock_minimo  # Devuelve True si está por debajo del stock mínimo

    def necesita_advertencia(self):  # Método para verificar si se necesita emitir una advertencia sobre el stock
        if self.verificar_stock_minimo():  # Comprueba si se está por debajo del stock mínimo
                return True  # Devuelve True si necesita advertencia
        return False  # Devuelve False si no necesita advertencia

    def __str__(self):  # Método para representar el objeto como una cadena
        return f"{self.referencia} - {self.descripcion} - Cantidad Restante: {self.cantidad_restante}"

    class Meta:
        db_table = 'cables'  # Nombre de la tabla en la base de datos

# Modelo para mensajes de prueba en el sistema
class MensajePruebaDP(models.Model):
    mensaje = models.TextField()  # Campo para almacenar el mensaje de texto
    fecha = models.DateTimeField(auto_now_add=True)  # Fecha y hora en que se creó el mensaje, se establece automáticamente

    def __str__(self):
        # Método para representar el objeto como una cadena
        return f"Mensaje Prueba-DP recibido el {self.fecha}: {self.mensaje}"

    class Meta:
        db_table = 'topic1'  # Nombre de la tabla en la base de datos
        
# Modelo para registrar la dispensación de cables
class RegistroDispensa(models.Model):
    cable = models.ForeignKey(Cables, on_delete=models.CASCADE)  # Relación con el modelo de Cables, eliminando registros relacionados si el cable es eliminado
    cantidad_dispensada = models.FloatField()  # Cantidad de cable dispensada, almacenada como un número de punto flotante
    fecha = models.DateTimeField(auto_now_add=True)  # Fecha y hora de la dispensación, se establece automáticamente al crear el registro
    proyecto = models.ForeignKey(Proyectos, on_delete=models.CASCADE)  # Relación con el modelo Proyectos, eliminando registros relacionados si el proyecto es eliminado
    tablero = models.ForeignKey(Tableros, on_delete=models.CASCADE)  # Relación con el modelo Tableros, eliminando registros relacionados si el tablero es eliminado
    cantidad_restante_despues = models.IntegerField(default=0)  # Cantidad restante de cable después de la dispensación, con un valor predeterminado de 0
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, null=True)  # Relación con el modelo Usuarios, permitiendo que sea nulo
    reproceso = models.BooleanField(default=False)  # Indica si es reproceso

    def __str__(self):
        # Devuelve una representación legible del objeto
        return f"{self.cantidad_dispensada} metros de cable dispensados el {self.fecha} para el proyecto {self.proyecto} en el tablero {self.tablero}"

    class Meta:
        db_table = 'registro_dispensas'  # Nombre de la tabla en la base de datos


# Modelo para almacenar direcciones de correo electrónico de destinatarios
class DestinatarioCorreo(models.Model):
    correo = models.EmailField(unique=True)  # Campo para almacenar un correo electrónico único

    def __str__(self):
        # Devuelve la dirección de correo almacenada
        return self.correo
    
class ConfiguracionCable(models.Model):
    cable = models.ForeignKey(Cables, on_delete=models.CASCADE)  # Esto significa que cada configuración de cable estará asociada a un cable específico
    esp = models.CharField(max_length=100)  # Se define como un campo de texto con un máximo de 100 caracteres.
    encoder = models.CharField(max_length=100) # También se define como un campo de texto con un máximo de 100 caracteres.

    class Meta:
        db_table = 'configuracion_cables' 
        unique_together = ('cable', 'esp', 'encoder')  # Asegura que la combinación de cable, esp y encoder sea única
        
    def __str__(self):
        return f'{self.cable} - ESP: {self.esp}, Encoder: {self.encoder}'  # Se utiliza para mostrar información sobre la configuración de cable
    

class Cola(models.Model):
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    tablero = models.ForeignKey(Tableros, on_delete=models.CASCADE)
    en_proceso = models.BooleanField(default=False)  # Indica si el usuario está dispensando actualmente
    fecha_creacion = models.DateTimeField(auto_now_add=True)