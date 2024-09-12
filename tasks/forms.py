from django import forms
from .models import Usuarios, Proyectos, Tableros, Cables
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class LoginForm(forms.Form):
    nombre_usuario = forms.CharField(max_length=50, label='Nombre de usuario')
    contraseña = forms.CharField(widget=forms.PasswordInput, label='Contraseña')
    
class UsuarioForm(forms.ModelForm):
    ROLES = [
        ('superadmin', 'SuperAdmin'),
        ('admin', 'Administrador'),
        ('operario', 'Operario'),
        ('auditor', 'Auditor')
    ]

    contraseña = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Ingrese una nueva contraseña solo si desea cambiarla."
    )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.request = request

        if self.instance.pk:
            self.fields['contraseña'].required = False

        if self.request:
            user_role = self.request.COOKIES.get('user_role')

            if user_role == 'admin':
                self.fields['rol'].choices = [
                    ('operario', 'Operario'),
                    ('auditor', 'Auditor')
                ]
                if self.instance.rol == 'admin':
                    self.fields['rol'].disabled = True
            elif user_role == 'superadmin':
                self.fields['rol'].choices = [
                    ('admin', 'Administrador'),
                    ('operario', 'Operario'),
                    ('auditor', 'Auditor')
                ]
                # Make the field read-only if the user being edited is a superadmin
                if self.instance.rol == 'superadmin':
                    self.fields['rol'].disabled = True
                    self.fields['rol'].widget = forms.TextInput(attrs={'readonly': 'readonly'})
            else:
                self.fields['rol'].choices = self.ROLES

    class Meta:
        model = Usuarios
        fields = ['cedula', 'nombre_persona', 'nombre_usuario', 'contraseña', 'rol']
        labels = {
            'cedula': 'Cédula',
            'nombre_persona': 'Nombre Completo',
            'nombre_usuario': 'Nombre de Usuario',
            'contraseña': 'Contraseña',
            'rol': 'Rol',
        }

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')

        if cedula and (len(cedula) != 10 or not cedula.isdigit()):
            raise ValidationError("La cédula debe tener exactamente 10 dígitos.")

        return cedula

    def clean(self):
        cleaned_data = super().clean()
        contraseña = cleaned_data.get('contraseña')

        if not self.instance.pk and not contraseña:
            self.add_error('contraseña', 'La contraseña es obligatoria.')

        return cleaned_data

    def clean_rol(self):
        rol = self.cleaned_data.get('rol')
        if self.request:
            user_role = self.request.COOKIES.get('user_role')

            if user_role == 'admin' and rol in ['admin', 'superadmin']:
                raise forms.ValidationError('No tienes permisos para crear administradores o superadministradores.')

        return rol
        
class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyectos
        fields = ['numero', 'tipo_proyecto']
        labels = {
            'numero': _('Número de Proyecto'),
            'tipo_proyecto': _('Tipo de Proyecto'),
        }
        error_messages = {
            'numero': {
                'required': _("El número del proyecto es obligatorio."),
                'max_length': _("El número del proyecto debe tener entre 8 y 10 dígitos."),  # Sobrescribe el mensaje predeterminado
                'min_length': _("El número del proyecto debe tener entre 8 y 10 dígitos."),  # También para el mínimo
            },
            'tipo_proyecto': {
                'required': _("El tipo de proyecto es obligatorio."),
            },
        }

    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        
        # Validar que solo contenga números
        if not numero.isdigit():
            raise forms.ValidationError(_("El número del proyecto solo puede contener dígitos."))
        
        # Validar que tenga entre 8 y 10 dígitos
        if len(numero) < 8 or len(numero) > 10:
            raise forms.ValidationError(_("El número del proyecto debe tener entre 8 y 10 dígitos."))
        
        return numero

    def clean(self):
        cleaned_data = super().clean()
        numero = cleaned_data.get('numero')
        tipo_proyecto = cleaned_data.get('tipo_proyecto')

        if numero and tipo_proyecto:
            # Si se está editando una instancia existente, excluye esta instancia de la búsqueda de duplicados
            if self.instance and self.instance.pk:
                existing_projects = Proyectos.objects.exclude(proyecto=self.instance.proyecto).filter(
                    numero=numero,
                    tipo_proyecto=tipo_proyecto
                )
            else:
                existing_projects = Proyectos.objects.filter(
                    numero=numero,
                    tipo_proyecto=tipo_proyecto
                )
            if existing_projects.exists():
                self.add_error('numero', _("Ya existe un proyecto con este Número y Tipo de Proyecto."))

        return cleaned_data
        
class TablerosForm(forms.ModelForm):
    class Meta:
        model = Tableros
        fields = ['proyecto', 'item']
        labels = {
            'proyecto': 'Proyecto Asociado',
            'item': 'Item',
        }
        error_messages = {
            'proyecto': {
                'required': "El campo Proyecto Asociado es obligatorio.",
            },
            'item': {
                'required': "El campo Item es obligatorio.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proyecto'].queryset = Proyectos.objects.all()

    def clean_item(self):
        item = self.cleaned_data.get('item')

        # Verificar si el item es negativo
        if item is not None and item < 0:
            raise forms.ValidationError("El item no puede ser un número negativo.")

        return item

    def clean(self):
        cleaned_data = super().clean()
        proyecto = cleaned_data.get('proyecto')
        item = cleaned_data.get('item')

        if proyecto and item:
            # Si se está editando una instancia existente, excluye esta instancia de la búsqueda de duplicados
            if self.instance and self.instance.pk:
                existing_tableros = Tableros.objects.exclude(pk=self.instance.pk).filter(
                    proyecto=proyecto,
                    item=item
                )
            else:
                existing_tableros = Tableros.objects.filter(
                    proyecto=proyecto,
                    item=item
                )
            if existing_tableros.exists():
                self.add_error('item', "Ya existe un tablero con este item para el proyecto seleccionado.")

        return cleaned_data
                     
class CableForm(forms.ModelForm):
    class Meta:
        model = Cables
        fields = ['referencia', 'descripcion', 'cantidad_inicial', 'stock_minimo', 'ultima_advertencia']
        
        # Configuración de widgets para los campos del formulario
        widgets = {
            'referencia': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ingrese la referencia del cable'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ingrese la descripción del cable'
            }),
            'cantidad_inicial': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ingrese la cantidad inicial'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ingrese el stock mínimo permitido'
            }),
            'ultima_advertencia': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Última advertencia',
                'type': 'datetime-local'
            }),
        }

        # Etiquetas para los campos del formulario
        labels = {
            'referencia': 'Referencia',
            'descripcion': 'Descripción',
            'cantidad_inicial': 'Cantidad Inicial',
            'stock_minimo': 'Stock Mínimo',
            'ultima_advertencia': 'Última Advertencia',
        }

    def clean(self):
        cleaned_data = super().clean()
        cantidad_inicial = cleaned_data.get("cantidad_inicial")
        stock_minimo = cleaned_data.get("stock_minimo")

        if cantidad_inicial is not None and stock_minimo is not None:
            if cantidad_inicial < stock_minimo:
                self.add_error('cantidad_inicial', 'La cantidad inicial no puede ser menor que el stock mínimo.')
                
        return cleaned_data
        
