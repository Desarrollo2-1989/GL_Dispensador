from django import forms  # Importa la clase forms para crear formularios en Django
from .models import (
    Usuarios,
    Proyectos,
    Tableros,
    Cables,
    DestinatarioCorreo,
    ConfiguracionCable,
)  # Importa los modelos necesarios para el formulario
from django.utils.translation import (
    gettext_lazy as _,
)  # Importa la función para la traducción de textos
from django.core.exceptions import (
    ValidationError,
)  # Importa la clase para manejar errores de validación


# Formulario de inicio de sesión
class LoginForm(forms.Form):
    # Campo para el nombre de usuario
    nombre_usuario = forms.CharField(max_length=50, label="Nombre de usuario")
    # Campo para la contraseña
    contraseña = forms.CharField(widget=forms.PasswordInput, label="Contraseña")


# Formulario para crear/editar un usuario
class UsuarioForm(forms.ModelForm):
    # Opciones para el rol del usuario
    ROLES = [
        ("superadmin", "SuperAdmin"),
        ("admin", "Administrador"),
        ("operario", "Operario"),
        ("auditor", "Auditor"),
    ]

    # Campo para la contraseña (opcional)
    contraseña = forms.CharField(
        widget=forms.PasswordInput,  # Utiliza un campo de entrada para contraseña
        required=False,  # Este campo no es obligatorio
        help_text="Ingrese una nueva contraseña solo si desea cambiarla.",  # Texto de ayuda
    )

    # Método para inicializar el formulario
    def __init__(self, *args, **kwargs):
        request = kwargs.pop(
            "request", None
        )  # Extrae el objeto de solicitud del argumento
        super().__init__(*args, **kwargs)  # Llama al inicializador de la clase padre
        self.request = request  # Almacena la solicitud para uso posterior

        if self.instance.pk:  # Si se está editando un usuario existente
            self.fields["contraseña"].required = (
                False  # No hacer obligatoria la contraseña
            )

        if self.request:  # Si hay una solicitud
            user_role = self.request.COOKIES.get(
                "user_role"
            )  # Obtiene el rol del usuario de las cookies

            if user_role == "admin":  # Si el rol del usuario es 'admin'
                self.fields["rol"].choices = [  # Define opciones de rol limitadas
                    ("operario", "Operario"),
                    ("auditor", "Auditor"),
                ]
                if self.instance.rol == "admin":  # Si el usuario es admin
                    self.fields["rol"].disabled = True  # Desactiva el campo rol
            elif user_role == "superadmin":  # Si el rol del usuario es 'superadmin'
                self.fields["rol"].choices = [  # Define opciones de rol
                    ("admin", "Administrador"),
                    ("operario", "Operario"),
                    ("auditor", "Auditor"),
                ]
                if self.instance.rol == "superadmin":  # Si el usuario es superadmin
                    self.fields["rol"].disabled = True  # Desactiva el campo rol
                    self.fields["rol"].widget = (
                        forms.TextInput(  # Establece el campo como de solo lectura
                            attrs={"readonly": "readonly"}
                        )
                    )
            else:  # Para otros roles
                self.fields["rol"].choices = (
                    self.ROLES
                )  # Usa las opciones definidas anteriormente

    class Meta:
        model = Usuarios  # Modelo asociado a este formulario
        fields = [  # Campos que se incluirán en el formulario
            "cedula",
            "nombre_persona",
            "nombre_usuario",
            "contraseña",
            "rol",
            "estado",
        ]
        labels = {  # Etiquetas para los campos del formulario
            "cedula": "Cédula",
            "nombre_persona": "Nombre Completo",
            "nombre_usuario": "Nombre de Usuario",
            "contraseña": "Contraseña",
            "rol": "Rol",
            "estado": "Estado",
        }

    def clean_cedula(self):  # Método para validar el campo 'cedula'
        cedula = self.cleaned_data.get("cedula")  # Obtiene la cédula limpiada
        if cedula and (
            len(cedula) < 6 or not cedula.isdigit()
        ):  # Verifica si la cédula es válida
            raise ValidationError(
                "La cédula debe tener al menos 6 dígitos."
            )  # Lanza un error si no es válida
        return cedula  # Retorna la cédula validada

    def clean(self):  # Método para limpiar los datos del formulario
        cleaned_data = super().clean()  # Llama al método de la clase padre
        contraseña = cleaned_data.get("contraseña")  # Obtiene la contraseña limpiada
        if (
            not self.instance.pk and not contraseña
        ):  # Si se está creando un nuevo usuario sin contraseña
            self.add_error(
                "contraseña", "La contraseña es obligatoria."
            )  # Lanza un error
        return cleaned_data  # Retorna los datos limpiados

    def clean_rol(self):  # Método para validar el campo 'rol'
        rol = self.cleaned_data.get("rol")  # Obtiene el rol limpiado
        if self.request:  # Si hay una solicitud
            user_role = self.request.COOKIES.get(
                "user_role"
            )  # Obtiene el rol del usuario
            if user_role == "admin" and rol in [
                "admin",
                "superadmin",
            ]:  # Si un admin intenta crear otro admin o superadmin
                raise forms.ValidationError(  # Lanza un error de validación
                    "No tienes permisos para crear administradores o superadministradores."
                )
        return rol  # Retorna el rol validado


# Formulario para crear/editar un proyecto
class ProyectoForm(forms.ModelForm):
    # Configuración del formulario
    class Meta:
        model = Proyectos  # Modelo asociado a este formulario
        fields = ["numero", "tipo_proyecto"]  # Campos que se incluirán en el formulario
        labels = {  # Etiquetas para los campos del formulario
            "numero": _("Número de Proyecto"),
            "tipo_proyecto": _("Tipo de Proyecto"),
        }
        error_messages = {  # Mensajes de error personalizados para los campos
            "numero": {
                "required": _("El número del proyecto es obligatorio."),
            },
            "tipo_proyecto": {
                "required": _("El tipo de proyecto es obligatorio."),
            },
        }

    # Método para validar el número del proyecto
    def clean_numero(self):
        numero = self.cleaned_data.get("numero")  # Obtiene el número limpiado

        # Validar que solo contenga números
        if not numero.isdigit():  # Verifica si el número contiene solo dígitos
            raise forms.ValidationError(
                _(
                    "El número del proyecto solo puede contener dígitos."
                )  # Lanza un error si no es válido
            )

        # Validar que tenga entre 8 y 10 dígitos
        if len(numero) < 6 or len(numero) > 7:  # Verifica la longitud del número
            raise forms.ValidationError(
                _(
                    "El número del proyecto debe tener entre 6 y 7 dígitos."
                )  # Lanza un error si la longitud es incorrecta
            )

        return numero  # Retorna el número validado

    # Método para validar la existencia de un proyecto con el mismo número y tipo
    def clean(self):
        cleaned_data = super().clean()  # Llama al método de la clase padre
        numero = cleaned_data.get("numero")  # Obtiene el número limpiado
        tipo_proyecto = cleaned_data.get(
            "tipo_proyecto"
        )  # Obtiene el tipo de proyecto limpiado

        if numero and tipo_proyecto:  # Si ambos campos están presentes
            # Si se está editando una instancia existente, excluye esta instancia de la búsqueda de duplicados
            if (
                self.instance and self.instance.pk
            ):  # Verifica si hay una instancia existente
                existing_projects = Proyectos.objects.exclude(
                    proyecto=self.instance.proyecto  # Excluye la instancia actual de la búsqueda
                ).filter(
                    numero=numero, tipo_proyecto=tipo_proyecto
                )  # Filtra por número y tipo de proyecto
            else:
                existing_projects = Proyectos.objects.filter(  # Filtra por número y tipo de proyecto si no hay instancia
                    numero=numero, tipo_proyecto=tipo_proyecto
                )
            if (
                existing_projects.exists()
            ):  # Verifica si ya existen proyectos con el mismo número y tipo
                self.add_error(
                    "numero",
                    _(
                        "Ya existe un proyecto con este Número y Tipo de Proyecto."
                    ),  # Lanza un error si hay duplicados
                )

        return cleaned_data  # Retorna los datos limpiados


# Formulario para crear/editar un tablero
class TablerosForm(forms.ModelForm):
    # Configuración del formulario
    class Meta:
        model = Tableros  # Modelo asociado a este formulario
        fields = ["proyecto", "item"]  # Campos que se incluirán en el formulario
        labels = {  # Etiquetas para los campos del formulario
            "proyecto": "Proyecto Asociado",
            "item": "Item",
        }
        error_messages = {  # Mensajes de error personalizados para los campos
            "proyecto": {
                "required": "El campo Proyecto Asociado es obligatorio.",  # Mensaje si el campo es requerido
            },
            "item": {
                "required": "El campo Item es obligatorio.",  # Mensaje si el campo es requerido
            },
        }

    # Método para inicializar el formulario
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Llama al inicializador de la clase padre
        self.fields["proyecto"].queryset = (
            Proyectos.objects.all()
        )  # Establece el queryset para el campo proyecto

    # Método para validar el item
    def clean_item(self):
        item = self.cleaned_data.get("item")  # Obtiene el item limpiado

        # Verificar si el item es negativo
        if item is not None and item < 0:  # Verifica si el item es un número negativo
            raise forms.ValidationError(
                "El item no puede ser un número negativo."
            )  # Lanza un error si es negativo

        return item  # Retorna el item validado

    # Método para validar la existencia de un tablero con el mismo proyecto y item
    def clean(self):
        cleaned_data = super().clean()  # Llama al método de la clase padre
        proyecto = cleaned_data.get("proyecto")  # Obtiene el proyecto limpiado
        item = cleaned_data.get("item")  # Obtiene el item limpiado

        if proyecto and item:  # Si ambos campos están presentes
            # Si se está editando una instancia existente, excluye esta instancia de la búsqueda de duplicados
            if (
                self.instance and self.instance.pk
            ):  # Verifica si hay una instancia existente
                existing_tableros = Tableros.objects.exclude(
                    pk=self.instance.pk  # Excluye la instancia actual de la búsqueda
                ).filter(
                    proyecto=proyecto, item=item
                )  # Filtra por proyecto y item
            else:
                existing_tableros = Tableros.objects.filter(  # Filtra por proyecto y item si no hay instancia
                    proyecto=proyecto, item=item
                )
            if (
                existing_tableros.exists()
            ):  # Verifica si ya existen tableros con el mismo proyecto y item
                self.add_error(
                    "item",
                    "Ya existe un tablero con este item para el proyecto seleccionado.",  # Lanza un error si hay duplicados
                )

        return cleaned_data  # Retorna los datos limpiados


# Formulario para crear/editar un cable
class CableForm(forms.ModelForm):
    # Configuración del formulario
    class Meta:
        model = Cables  # Modelo asociado a este formulario
        fields = [  # Campos que se incluirán en el formulario
            "referencia",
            "descripcion",
            "cantidad_inicial",
            "stock_minimo",
            "ultima_advertencia",
        ]

        # Configuración de widgets para los campos del formulario
        widgets = {  # Widgets personalizados para los campos
            "referencia": forms.NumberInput(  # Widget para el campo de referencia
                attrs={
                    "class": "form-control",  # Clase CSS para el estilo
                    "placeholder": "Ingrese la referencia del cable",  # Texto de ayuda
                }
            ),
            "descripcion": forms.TextInput(  # Widget para el campo de descripción
                attrs={
                    "class": "form-control",  # Clase CSS para el estilo
                    "placeholder": "Ingrese la descripción del cable",  # Texto de ayuda
                }
            ),
            "cantidad_inicial": forms.NumberInput(  # Widget para el campo de cantidad inicial
                attrs={
                    "class": "form-control",  # Clase CSS para el estilo
                    "placeholder": "Ingrese la cantidad inicial",  # Texto de ayuda
                }
            ),
            "stock_minimo": forms.NumberInput(  # Widget para el campo de stock mínimo
                attrs={
                    "class": "form-control",  # Clase CSS para el estilo
                    "placeholder": "Ingrese el stock mínimo permitido",  # Texto de ayuda
                }
            ),
            "ultima_advertencia": forms.DateTimeInput(  # Widget para el campo de última advertencia
                attrs={
                    "class": "form-control",  # Clase CSS para el estilo
                    "placeholder": "Última advertencia",  # Texto de ayuda
                    "type": "datetime-local",  # Tipo de input para fecha y hora
                }
            ),
        }

        # Etiquetas para los campos del formulario
        labels = {  # Etiquetas personalizadas para los campos
            "referencia": "Referencia",
            "descripcion": "Descripción",
            "cantidad_inicial": "Cantidad Inicial",
            "stock_minimo": "Stock Mínimo",
            "ultima_advertencia": "Última Advertencia",
        }

    # Método para validar la cantidad inicial y el stock mínimo
    def clean(self):
        cleaned_data = super().clean()  # Llama al método de limpieza de la clase padre
        cantidad_inicial = cleaned_data.get(
            "cantidad_inicial"
        )  # Obtiene la cantidad inicial limpiada
        stock_minimo = cleaned_data.get(
            "stock_minimo"
        )  # Obtiene el stock mínimo limpiado

        if (
            cantidad_inicial is not None and stock_minimo is not None
        ):  # Si ambos campos están presentes
            if (
                cantidad_inicial < stock_minimo
            ):  # Verifica si la cantidad inicial es menor que el stock mínimo
                self.add_error(
                    "cantidad_inicial",
                    "La cantidad inicial no puede ser menor que el stock mínimo.",  # Lanza un error si es así
                )

        return cleaned_data  # Retorna los datos limpiados


class DestinatarioCorreoForm(forms.ModelForm):
    class Meta:
        model = DestinatarioCorreo  # Modelo asociado a este formulario
        fields = ["correo"]  # Campos que se incluirán en el formulario
        widgets = {  # Configuración de widgets para los campos del formulario
            "correo": forms.EmailInput(  # Widget para el campo de correo
                attrs={
                    "class": "form-control",  # Clase CSS para el estilo
                    "placeholder": "Ingrese el correo electrónico",  # Texto de ayuda
                }
            ),
        }
        error_messages = {  # Mensajes de error personalizados
            "correo": {
                "required": _(
                    "El Correo Electrónico es obligatorio."
                ),  # Mensaje si el campo es obligatorio
                "invalid": _(
                    "Ingrese un correo electrónico válido."
                ),  # Mensaje si el formato no es válido
                "unique": _(
                    "Este correo ya está registrado."
                ),  # Mensaje si el correo ya existe
            },
        }

    def clean_correo(self):
        correo = self.cleaned_data.get("correo")  # Obtiene el correo limpiado
        destinatario_id = self.instance.id  # Obtiene el ID del destinatario (si existe)

        # Validar que no se repita el correo
        if (
            DestinatarioCorreo.objects.exclude(
                id=destinatario_id
            )  # Excluye el destinatario actual de la búsqueda
            .filter(correo=correo)  # Filtra por el correo ingresado
            .exists()  # Verifica si existe algún registro con el mismo correo
        ):
            raise forms.ValidationError(
                self.Meta.error_messages["correo"]["unique"]
            )  # Lanza un error si el correo ya está registrado

        return correo  # Retorna el correo limpio

class ConfiguracionCableForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionCable
        fields = ["cable", "esp", "encoder"]
        labels = {
            "cable": _("Cable"),
            "esp": _("ESP"),
            "encoder": _("Encoder"),
        }
        error_messages = {
            "cable": {
                "required": _("El campo Cable es obligatorio."),
            },
            "esp": {
                "required": _("El campo ESP es obligatorio."),
            },
            "encoder": {
                "required": _("El campo Encoder es obligatorio."),
            },
        }

    def clean_esp(self):
        esp = self.cleaned_data.get("esp")
        if not esp:
            raise forms.ValidationError(_("El campo ESP es obligatorio."))
        return esp

    def clean_encoder(self):
        encoder = self.cleaned_data.get("encoder")
        if not encoder:
            raise forms.ValidationError(_("El campo Encoder es obligatorio."))
        return encoder

    def clean(self):
        cleaned_data = super().clean()
        cable = cleaned_data.get("cable")
        esp = cleaned_data.get("esp")
        encoder = cleaned_data.get("encoder")
        current_id = self.instance.id  # Obtener el ID de la instancia actual

        # Validar que no existan duplicados para el campo 'cable'
        if cable and ConfiguracionCable.objects.filter(cable=cable).exclude(id=current_id).exists():
            self.add_error("cable", _("Ya existe una configuración con este Cable."))

        # Validar que no haya una combinación duplicada de ESP y Encoder
        if esp and encoder:
            if ConfiguracionCable.objects.filter(esp=esp, encoder=encoder).exclude(id=current_id).exists():
                self.add_error("encoder", _("Este encoder ya está asignado al ESP seleccionado."))
        
        return cleaned_data
