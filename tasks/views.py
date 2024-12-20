# get_template permite cargar plantillas manualmente en Django
from django.template.loader import get_template
# chardet para detectar la codificación de caracteres en archivos
import chardet
# timezone para manejar zonas horarias en aplicaciones Django
from django.utils import timezone 
# render, redirect y get_object_or_404 son funciones auxiliares para el manejo de vistas y redirecciones en Django
from django.shortcuts import render, redirect, get_object_or_404
# messages se utiliza para enviar mensajes de éxito o error al usuario
from django.contrib import messages
# Paginator permite dividir en páginas grandes listas de datos en Django
from django.core.paginator import Paginator
# Q se utiliza para realizar consultas más complejas en la base de datos
from django.db.models import Q
# Importación de modelos propios de la aplicación
from .models import Usuarios, Proyectos, Tableros, Cables, MensajePruebaDP, RegistroDispensa, DestinatarioCorreo, ConfiguracionCable, Cola
# Importación de formularios propios de la aplicación
from .forms import LoginForm, UsuarioForm, ProyectoForm, TablerosForm, CableForm, DestinatarioCorreoForm, ConfiguracionCableForm
# IntegrityError para manejar errores de integridad de la base de datos
from django.db import IntegrityError
# make_password y check_password para encriptar y verificar contraseñas
from django.contrib.auth.hashers import make_password, check_password
# transaction para manejo de transacciones de base de datos en Django
from django.db import transaction
# csv para manejo de archivos CSV
import csv
# Importación de decoradores personalizados para verificación de roles
from .decorators import verificar_rol
# io para trabajar con flujos de entrada y salida
import io
# send_mail permite el envío de correos electrónicos
from django.core.mail import send_mail
# Importación del cliente MQTT para la comunicación mediante el protocolo MQTT
import paho.mqtt.client as mqtt
# Sum para realizar operaciones de agregación en consultas de base de datos
from django.db.models import Sum
# json para manejar datos en formato JSON
import json
from django.utils.dateparse import parse_date
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache



def login(request):
    # Verifica si la solicitud es de tipo POST
    if request.method == 'POST':
        # Crea una instancia del formulario de inicio de sesión con los datos recibidos
        form = LoginForm(request.POST)
        # Verifica si el formulario es válido
        if form.is_valid():
            # Obtiene el nombre de usuario y la contraseña ingresados
            nombre_usuario = form.cleaned_data['nombre_usuario']
            contraseña = form.cleaned_data['contraseña']
            try:
                # Busca en la base de datos el usuario con el nombre ingresado
                user = Usuarios.objects.get(nombre_usuario=nombre_usuario)

                # Verifica si el usuario está activo
                if not user.estado:
                    messages.error(request, "El usuario está inactivo.")
                    return render(request, 'login.html', {'form': form})

                # Verifica si la contraseña ingresada coincide con la del usuario
                if check_password(contraseña, user.contraseña):
                    # Redirecciona al usuario según su rol
                    if user.rol == 'superadmin':
                        response = redirect('administrar_usuarios')
                    elif user.rol == 'admin':
                        response = redirect('administrar_usuarios')
                    elif user.rol == 'operario':
                        response = redirect('operario')
                    else:
                        response = redirect('registros')

                    # Guardar el rol y cédula en la sesión
                    # Redirigir según rol
                    request.session['user_cedula'] = user.cedula
                    request.session['user_name'] = user.nombre_persona
                    request.session['user_role'] = user.rol        
                    return response
                else:
                    # Muestra un mensaje de error si la contraseña es incorrecta
                    messages.error(request, "Contraseña incorrecta.")
            except Usuarios.DoesNotExist:
                # Muestra un mensaje de error si el usuario no existe
                messages.error(request, "El usuario no existe.")
    else:
        # Si el método no es POST, crea un formulario vacío
        form = LoginForm()

    # Renderiza la vista de inicio de sesión
    return render(request, 'login.html', {'form': form})

def logout(request):
    # Redirige a la página de login y elimina la sesión
    response = redirect('login')
    request.session.flush()  # Elimina todas las variables de sesión
    return response

def superAdmin(request):
    # Verificar si el usuario tiene una sesión válida y un rol de superadministrador
    if not  request.session.get('user_cedula') or  request.session.get('user_role') != 'superadmin':
        # Si no se encuentra la cédula en session o el rol no es 'superadmin', redirige a la página de login
        return redirect('login')
    # Renderizar la página base para el rol de superadministrador
    return render(request, 'adminlte/base.html')

def administrador(request):
    # Verificar si el usuario tiene una sesión válida y un rol de administrador
    if not request.session.get('user_cedula') or request.session.get('user_role') != 'admin':
        return redirect('login')
    return render(request, 'adminlte/base.html')


# CRUD PARA CREAR USUARIO  
@verificar_rol('admin', 'superadmin')  # Verifica que el rol del usuario tenga permisos de acceso
def crear_usuario(request):
    # Verifica si la solicitud es de tipo POST para procesar la creación de un nuevo usuario
    if request.method == 'POST':
        form = UsuarioForm(request.POST, request=request)  # Instancia el formulario con los datos proporcionados en la solicitud
        if form.is_valid():  # Verifica que los datos del formulario sean válidos
            try:
                usuario = form.save(commit=False)  # Crea un objeto de usuario sin guardarlo aún en la base de datos
                usuario.contraseña = make_password(usuario.contraseña)  # Encripta la contraseña antes de guardarla

                # Verifica el rol antes de guardar
                user_role = request.session.get('user_role')  # Obtiene el rol del usuario de session
                if user_role == 'admin' and usuario.rol in ['admin', 'superadmin']:
                    # Si el usuario es un administrador y trata de crear otro admin o superadmin, muestra un mensaje de error
                    messages.error(request, 'No tienes permisos para crear administradores o superadministradores.')
                    return redirect('crear_usuario')

                usuario.save()  # Guarda el nuevo usuario en la base de datos
                messages.success(request, 'Usuario creado exitosamente.')  # Muestra un mensaje de éxito
                return redirect('administrar_usuarios')  # Redirige a la vista de administración de usuarios
            except IntegrityError:  # Maneja errores de integridad, como duplicados
                if 'nombre_usuario' in form.errors:  # Verifica si el nombre de usuario ya existe
                    form.add_error('nombre_usuario', 'Ya existe un usuario con este nombre de usuario.')
                if 'cedula' in form.errors:  # Verifica si la cédula ya existe
                    form.add_error('cedula', 'Ya existe un usuario con esta cédula.')
    else:
        form = UsuarioForm(request=request)  # Crea una instancia de UsuarioForm en caso de solicitud GET

    # Renderiza el formulario de creación de usuario
    return render(request, 'usuarios/crear_usuario.html', {'form': form})

@verificar_rol('admin', 'superadmin')  # Decorador que verifica que el usuario tenga rol de admin o superadmin
def editar_usuario(request, cedula):
    usuario = get_object_or_404(Usuarios, cedula=cedula)  # Obtiene el usuario con la cédula especificada o lanza un error 404 si no existe
    current_user_role = request.session.get('user_role')  # Obtiene el rol del usuario actual de session
    current_user_cedula = request.session.get('user_cedula')  # Obtiene la cédula del usuario actual de las session

    # Verifica si el usuario actual es admin intentando editar a otro admin o superadmin
    if current_user_role == 'admin' and (usuario.rol == 'superadmin' or usuario.rol == 'admin'):
        messages.error(request, 'No tiene permiso para editar a otro administrador o superadmin.')
        return redirect('administrar_usuarios')  # Redirige a la vista de administración de usuarios si no tiene permisos

    # Cuenta cuántos administradores activos existen en el sistema
    admin_count = Usuarios.objects.filter(rol='admin', estado=True).count()

    # Procesa la solicitud POST si se intenta actualizar el usuario
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario, request=request)  # Inicializa el formulario con los datos de POST y del usuario actual
        if form.is_valid():  # Verifica que el formulario sea válido
            try:
                usuario = form.save(commit=False)  # Guarda el formulario sin comprometerlo en la base de datos aún

                # Cifra la contraseña solo si ha sido modificada en el formulario
                if form.cleaned_data.get('contraseña'):
                    usuario.contraseña = make_password(form.cleaned_data['contraseña'])
                else:
                    # Mantiene la contraseña actual si no se proporciona una nueva
                    usuario.contraseña = Usuarios.objects.get(cedula=cedula).contraseña

                # Bloquea el cambio de rol si el usuario es superadmin para mantener su rol original
                if usuario.rol == 'superadmin':
                    usuario.rol = Usuarios.objects.get(cedula=cedula).rol

                # Asegura que el superadmin siempre esté activo
                if usuario.rol == 'superadmin':
                    usuario.estado = True

                # Verifica si se intenta inactivar el último administrador activo
                if usuario.rol == 'admin' and form.cleaned_data.get('estado') == False and admin_count <= 1:
                    messages.error(request, 'Debe haber al menos un administrador activo.')
                    return redirect('administrar_usuarios')

                usuario.save()  # Guarda el usuario en la base de datos
                messages.success(request, 'Usuario actualizado exitosamente')  # Muestra mensaje de éxito

                # Actualiza session si el usuario editado es el usuario autenticado actual
                if current_user_cedula == usuario.cedula:
                    response = redirect('administrar_usuarios')
                    request.session('user_role', usuario.rol)  # Actualiza el rol en la session
                    request.session('user_name', usuario.nombre_persona)  # Actualiza el nombre en la session
                    return response

                return redirect('administrar_usuarios')  # Redirige a la vista de administración de usuarios
            except IntegrityError:  # Maneja errores de integridad, como nombres de usuario duplicados
                messages.error(request, 'Error al actualizar el usuario.')
    else:
        form = UsuarioForm(instance=usuario, request=request)  # Crea una instancia del formulario en caso de solicitud GET

    # Renderiza el formulario de edición del usuario con el conteo de administradores activos
    return render(request, 'usuarios/editar_usuario.html', {'form': form, 'admin_count': admin_count})

@verificar_rol('admin', 'superadmin')  # Decorador que verifica que el usuario tenga rol de admin o superadmin
def eliminar_usuario(request, cedula):
    usuario = get_object_or_404(Usuarios, cedula=cedula)  # Obtiene el usuario a eliminar o muestra un error 404 si no existe
    user_role = request.session.get('user_role')  # Obtiene el rol del usuario autenticado desde session

    # Verifica si el usuario a eliminar es el superadministrador
    if usuario.rol == 'superadmin':
        messages.error(request, 'No se puede eliminar al superadministrador.')  # Mensaje de error si se intenta eliminar al superadmin
        return redirect('administrar_usuarios')  # Redirige a la vista de administración de usuarios

    # Verifica si el usuario a eliminar es un administrador
    if usuario.rol == 'admin':
        # Cuenta cuántos administradores activos existen en el sistema
        admin_count = Usuarios.objects.filter(rol='admin', estado=True).count()
        # Verifica si el usuario a eliminar es el último administrador activo
        if usuario.estado and admin_count <= 1:
            messages.error(request, 'Debe haber al menos un administrador activo.')  # Mensaje de error si es el último admin activo
            return redirect('administrar_usuarios')

    # Procesa la solicitud POST si se confirma la eliminación del usuario
    if request.method == 'POST':
        usuario.delete()  # Elimina el usuario de la base de datos
        messages.success(request, 'El usuario ha sido eliminado correctamente.')  # Mensaje de éxito tras la eliminación
        return redirect('administrar_usuarios')  # Redirige a la vista de administración de usuarios

    # Renderiza la página de confirmación de eliminación con los datos del usuario a eliminar
    return render(request, 'eliminar_usuario.html', {'usuario': usuario})

@verificar_rol('admin', 'superadmin')  # Decorador para verificar que el usuario tiene rol de admin o superadmin
def administrar_usuarios(request):
    query = request.GET.get('q')  # Obtiene el valor de búsqueda desde los parámetros GET
    user_role = request.session.get('user_role')  # Obtiene el rol del usuario autenticado desde las session
    
    # Realiza la búsqueda de usuarios según la consulta de búsqueda y el rol del usuario
    if query:
        if user_role == 'admin':
            usuarios = Usuarios.objects.filter(
                Q(cedula__icontains=query) |  # Búsqueda por cédula
                Q(nombre_persona__icontains=query) |  # Búsqueda por nombre de la persona
                Q(nombre_usuario__icontains=query) |  # Búsqueda por nombre de usuario
                Q(rol__icontains=query),  # Búsqueda por rol
                Q(rol='operario') | Q(rol='auditor')  # Filtro para mostrar solo roles de operario o auditor para admin
            ).order_by('nombre_usuario')  # Ordena los resultados por nombre de usuario
        else:  # Si el usuario es superadmin
            usuarios = Usuarios.objects.filter(
                Q(cedula__icontains=query) |
                Q(nombre_persona__icontains=query) |
                Q(nombre_usuario__icontains=query) |
                Q(rol__icontains=query),
            ).order_by('nombre_usuario')  # Muestra todos los roles para superadmin
    else:
        if user_role == 'admin':
            usuarios = Usuarios.objects.filter(
                Q(rol='operario') | Q(rol='auditor')  # Para admin, filtra usuarios de rol operario o auditor
            ).order_by('nombre_usuario')
        else:  # Para superadmin
            usuarios = Usuarios.objects.all().order_by('nombre_usuario')  # Muestra todos los usuarios

    paginator = Paginator(usuarios, 5)  # Configura la paginación para mostrar 5 usuarios por página
    page_number = request.GET.get('page')  # Obtiene el número de página actual desde los parámetros GET
    page_obj = paginator.get_page(page_number)  # Obtiene los usuarios de la página actual
    
    try:
        page_obj = paginator.page(page_number)  # Obtener la página correspondiente
    except PageNotAnInteger:
        page_obj = paginator.page(1)  # Si page no es un entero, muestra la primera página
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)  # Si page está fuera de los límites, muestra la última página

    context = {
        'page_obj': page_obj,  # Objeto de la página actual para el template
        'query': query,  # Incluye la consulta de búsqueda en el contexto para mantenerla en la vista
    }
    return render(request, 'usuarios/administrar_usuarios.html', context)  # Renderiza la plantilla con el contexto

# CRUD PROYECTO
@verificar_rol('admin', 'superadmin')  # Decorador para verificar que el usuario tiene el rol adecuado
def crear_proyecto(request):
    if request.method == 'POST':  # Verifica si el formulario fue enviado con método POST
        form = ProyectoForm(request.POST)  # Instancia el formulario con los datos enviados
        if form.is_valid():  # Verifica si el formulario es válido
            try:
                form.save()  # Guarda el proyecto en la base de datos
                messages.success(request, 'Proyecto creado exitosamente.')  # Mensaje de éxito
                return redirect('manejo_proyectos')  # Redirige a la vista de manejo de proyectos
            except IntegrityError:  # Captura errores de integridad (por ejemplo, duplicados)
                messages.error(request, 'Error al guardar el proyecto. Verifica los datos ingresados.')  # Mensaje de error
    else:
        form = ProyectoForm()  # Crea un formulario vacío si no es una solicitud POST

    return render(request, 'proyectos/crear_proyecto.html', {'form': form})  # Renderiza el formulario en la plantilla

@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def editar_proyecto(request, proyecto):
    # Obtener el proyecto a editar desde la base de datos
    proyecto_instance = get_object_or_404(Proyectos, proyecto=proyecto)

    # Manejar la solicitud POST para actualizar el proyecto
    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto_instance)  # Cargar datos en el formulario con la instancia actual del proyecto
        if form.is_valid():  # Validar el formulario
            try:
                form.save()  # Guardar los cambios en la base de datos
                messages.success(request, 'Proyecto actualizado exitosamente.')  # Mensaje de éxito
                return redirect('manejo_proyectos')  # Redirigir a la lista de proyectos
            except IntegrityError:  # Captura errores de integridad, por ejemplo, duplicados
                messages.error(request, 'Error al actualizar el proyecto. Verifica si el proyecto ya existe.')  # Mensaje de error
    else:
        form = ProyectoForm(instance=proyecto_instance)  # Crear el formulario con la instancia del proyecto si no es POST

    return render(request, 'proyectos/editar_proyecto.html', {'form': form})  # Renderiza la plantilla con el formulario

@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def eliminar_proyecto(request, proyecto):
    # Obtener el proyecto a eliminar desde la base de datos
    proyecto = get_object_or_404(Proyectos, proyecto=proyecto)
    
    # Manejar la solicitud POST para eliminar el proyecto
    if request.method == 'POST':
        proyecto.delete()  # Eliminar el proyecto de la base de datos
        messages.success(request, 'El proyecto ha sido eliminado correctamente.')  # Mensaje de éxito
        return redirect('manejo_proyectos')  # Redirigir a la lista de proyectos

    return render(request, 'proyectos/eliminar_proyecto.html', {'proyecto': proyecto})  # Renderiza la plantilla de confirmación

@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def manejo_proyectos(request):
    query = request.GET.get('q')  # Obtener la consulta de búsqueda
    if query:
        # Filtra los proyectos basados en la consulta
        proyectos = Proyectos.objects.filter(
            Q(proyecto__icontains=query) |
            Q(tipo_proyecto__icontains=query) |
            Q(numero__icontains=query)
        ).order_by('numero')  # Ordena por el campo 'numero'
    else:
        # Obtiene todos los proyectos y los ordena
        proyectos = Proyectos.objects.all().order_by('numero')  # Ordena por el campo 'numero'

    paginator = Paginator(proyectos, 5)  # Pagina los proyectos con 5 por página
    page_number = request.GET.get('page')  # Obtener el número de página de la solicitud
    page_obj = paginator.get_page(page_number)  # Obtiene los proyectos paginados
    
    try:
        page_obj = paginator.page(page_number)  # Obtener la página correspondiente
    except PageNotAnInteger:
        page_obj = paginator.page(1)  # Si page no es un entero, muestra la primera página
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)  # Si page está fuera de los límites, muestra la última página

    context = {
        'page_obj': page_obj,
        'query': query,  # Mantiene la consulta de búsqueda en el contexto
    }
    return render(request, 'proyectos/manejo_proyectos.html', context)  # Renderiza la plantilla de manejo de proyectos

# CRUD TABLERO 
@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def crear_tablero(request):
    if request.method == 'POST':  # Manejar la solicitud POST para crear un tablero
        form = TablerosForm(request.POST)  # Instancia del formulario con los datos recibidos
        if form.is_valid():  # Verifica si el formulario es válido
            try:
                with transaction.atomic():  # Iniciar una transacción atómica
                    form.save()  # Guarda el nuevo tablero en la base de datos
                    messages.success(request, 'Tablero creado exitosamente.')  # Mensaje de éxito
                    return redirect('tableros')  # Redirige a la lista de tableros
            except Exception as e:  # Captura cualquier excepción
                # Muestra un mensaje genérico si ocurre un error
                messages.error(request, 'Error al guardar el tablero. Verifique los datos ingresados.')
    else:
        form = TablerosForm()  # Crea una instancia vacía del formulario para la primera carga

    return render(request, 'tableros/crear_tablero.html', {'form': form})  # Renderiza la plantilla para crear un tablero

@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def editar_tablero(request, identificador):
    # Obtener el tablero a editar desde la base de datos
    tablero = get_object_or_404(Tableros, identificador=identificador)  # Busca el tablero por su identificador
    
    # Manejar la solicitud POST para actualizar el tablero
    if request.method == 'POST':  # Si la solicitud es de tipo POST
        form = TablerosForm(request.POST, instance=tablero)  # Instancia del formulario con los datos recibidos
        
        # Verificar si el formulario es válido
        if form.is_valid():  # Si el formulario es válido
            try:
                form.save()  # Guarda los cambios en el tablero
                messages.success(request, 'Tablero actualizado exitosamente.')  # Mensaje de éxito
                return redirect('tableros')  # Redirige a la lista de tableros
            except IntegrityError:
                form.add_error('item', 'Ya existe un tablero con este item para el proyecto seleccionado.')  # Manejo de error de integridad
    else:
        form = TablerosForm(instance=tablero)  # Crea una instancia del formulario con los datos actuales del tablero

    return render(request, 'tableros/editar_tablero.html', {'form': form})  # Renderiza la plantilla para editar un tablero

@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def eliminar_tablero(request, identificador):
    # Obtener el tablero a eliminar desde la base de datos
    tablero = get_object_or_404(Tableros, identificador=identificador)  # Busca el tablero por su identificador
    
    # Manejar la solicitud POST para eliminar el tablero
    if request.method == 'POST':  # Si la solicitud es de tipo POST
        # Eliminar el tablero
        tablero.delete()  # Elimina el tablero de la base de datos
        messages.success(request, 'El tablero ha sido eliminado correctamente.')  # Mensaje de éxito
        return redirect('tableros')  # Redirige a la lista de tableros

    return render(request, 'tableros/eliminar_tablero.html', {'tablero': tablero})  # Renderiza la plantilla para eliminar un tablero

@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def tableros(request):
    query = request.GET.get('q')  # Obtiene la consulta de búsqueda desde los parámetros GET
    if query:  # Si hay una consulta
        tableros = Tableros.objects.filter(
            Q(identificador__icontains=query)  # Filtra los tableros por el identificador
        ).order_by('proyecto', 'item')  # Ordena los resultados por proyecto e item
    else:
        tableros = Tableros.objects.all().order_by('proyecto', 'item')  # Obtiene todos los tableros ordenados

    paginator = Paginator(tableros, 5)  # Muestra 5 tableros por página
    page_number = request.GET.get('page')  # Obtiene el número de página desde los parámetros GET
    page_obj = paginator.get_page(page_number)  # Obtiene el objeto de página correspondiente
    
    try:
        page_obj = paginator.page(page_number)  # Obtener la página correspondiente
    except PageNotAnInteger:
        page_obj = paginator.page(1)  # Si page no es un entero, muestra la primera página
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)  # Si page está fuera de los límites, muestra la última página

    context = {
        'page_obj': page_obj,  # Objeto de página para la paginación
        'query': query,  # Mantener la consulta de búsqueda en el contexto
    }
    return render(request, 'tableros/tableros.html', context)  # Renderiza la plantilla con el contexto

@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def cargar_csv_tableros(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):  # Verifica si la solicitud es POST y se ha subido un archivo CSV
        csv_file = request.FILES['csv_file']  # Obtiene el archivo CSV subido
        
        try:
            # Leer el archivo CSV en memoria
            csv_data = csv_file.read()

            # Detectar la codificación del archivo CSV
            result = chardet.detect(csv_data)
            charenc = result['encoding']  # Obtiene la codificación del archivo

            # Decodificar el archivo CSV
            csv_data = csv_data.decode(charenc)

            # Leer los datos del archivo CSV
            reader = csv.DictReader(io.StringIO(csv_data), delimiter=';', quotechar='"', quoting=csv.QUOTE_NONE)

            # Listas para almacenar mensajes de éxito y de existencia
            created_messages = []
            existing_messages = []

            for row in reader:  # Itera sobre cada fila del CSV
                tipo_proyecto = row.get('Tipo')
                numero = row.get('Numero')
                item = row.get('Item')

                if not tipo_proyecto:  # Verifica si el tipo de proyecto está vacío
                    messages.error(request, f'El valor de Tipo es nulo o vacío en la fila {row}.')
                    return redirect('cargar_csv')

                # Crear o obtener el proyecto
                proyecto, _ = Proyectos.objects.get_or_create(
                    tipo_proyecto=tipo_proyecto,
                    numero=numero,
                    defaults={'proyecto': f"{tipo_proyecto}-{numero}"}
                )

                # Crear o obtener el tablero
                tablero, created = Tableros.objects.get_or_create(
                    proyecto=proyecto,
                    item=item,
                    defaults={'identificador': f"{proyecto.tipo_proyecto}-{proyecto.numero}-{item}"}
                )

                # Añadir el mensaje correspondiente a la lista adecuada
                if created:
                    created_messages.append(f'{tablero.identificador}. ')
                else:
                    existing_messages.append(f'{tablero.identificador}. ')

            # Mostrar los mensajes agrupados
            if created_messages:  # Si se han creado tableros, muestra el mensaje de éxito
                messages.success(request, "Tableros creados:\n" + "\n".join(created_messages))
            if existing_messages:  # Si ya existían tableros, muestra el mensaje informativo
                messages.info(request, "Tableros existentes:\n" + "\n".join(existing_messages))

        except Exception as e:  # Manejo de excepciones en caso de error
            messages.error(request, f'Error al cargar el archivo CSV: {e}')
            return redirect('cargar_csv')
    
    return render(request, 'tableros/cargar_csv.html')  # Renderiza la plantilla para cargar el CSV

#CRUD CABLE    
@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def crear_cable(request):
    if request.method == 'POST':  # Verifica si la solicitud es POST
        form = CableForm(request.POST)  # Crea una instancia del formulario con los datos recibidos
        if form.is_valid():  # Verifica si el formulario es válido
            try:
                # Guardar el cable y establecer cantidad_restante igual a cantidad_inicial
                setear_cable = form.save(commit=False)  # No guarda aún en la base de datos
                setear_cable.cantidad_restante = setear_cable.cantidad_inicial  # Asigna cantidad_restante
                setear_cable.save()  # Guarda el cable en la base de datos
                messages.success(request, 'Cable creado exitosamente.')  # Mensaje de éxito
                return redirect('cables')  # Redirige a la lista de cables
            except IntegrityError:
                messages.error(request, 'Error al guardar el cable. Verifica los datos ingresados.')  # Mensaje de error si hay un problema
    else:
        form = CableForm()  # Si no es una solicitud POST, crea un nuevo formulario
    
    return render(request, 'cables/crear_cable.html', {'form': form})  # Renderiza la plantilla para crear un cable

@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def editar_cable(request, referencia):
    cable = get_object_or_404(Cables, referencia=referencia)  # Obtener el cable por referencia o devolver 404 si no existe
    
    if request.method == 'POST':  # Verifica si la solicitud es POST
        form = CableForm(request.POST, instance=cable)  # Crea una instancia del formulario con los datos recibidos
        if form.is_valid():  # Verifica si el formulario es válido
            try:
                # Actualizar el cable sin modificar la cantidad restante
                cable = form.save(commit=False)  # No guarda aún en la base de datos
                cable.cantidad_restante = Cables.objects.get(referencia=referencia).cantidad_restante  # Mantener la cantidad restante actual
                cable.save()  # Guarda el cable en la base de datos
                messages.success(request, 'Cable actualizado exitosamente.')  # Mensaje de éxito
                return redirect('cables')  # Redirige a la lista de cables
            except IntegrityError:
                messages.error(request, 'Error al actualizar el cable. Verifica si el cable ya existe.')  # Mensaje de error si hay un problema
    else:
        form = CableForm(instance=cable)  # Si no es una solicitud POST, crea un formulario con los datos del cable existente
    
    return render(request, 'cables/editar_cable.html', {'form': form})  # Renderiza la plantilla para editar el cable


@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def reabastecer_cable(request, referencia):
    cable = get_object_or_404(Cables, referencia=referencia)  # Obtener el cable por referencia

    # La cantidad máxima que se puede reabastecer es la cantidad inicial
    cantidad_maxima_reabastecer = cable.cantidad_inicial

    if request.method == 'POST':
        cantidad_reabastecer = int(request.POST.get('cantidad_reabastecer', 0))
        
        # Verificar que la cantidad a reabastecer no supere la cantidad inicial
        if cantidad_reabastecer <= cantidad_maxima_reabastecer:
            cable.cantidad_restante = cantidad_reabastecer  # Actualizar la cantidad restante
            cable.save()  # Guardar los cambios
            messages.success(request, 'Cable reabastecido exitosamente.')  # Mensaje de éxito
            return redirect('cables')  # Redirigir a la lista de cables
        else:
            messages.error(request, 'La cantidad a reabastecer no puede superar la cantidad inicial.')  # Mensaje de error

    return render(request, 'cables/reabastecer_cable.html', {
        'cable': cable,
        'cantidad_maxima_reabastecer': cantidad_maxima_reabastecer  # Pasar la cantidad máxima al contexto
    })  # Renderizar la plantilla de reabastecimiento

@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def eliminar_cable(request, referencia):
    # Obtener el cable a eliminar desde la base de datos
    setear_cable = get_object_or_404(Cables, referencia=referencia)  # Busca el cable por referencia o devuelve 404 si no existe
    
    # Manejar la solicitud POST para eliminar el cable
    if request.method == 'POST':  # Verifica si la solicitud es POST
        setear_cable.delete()  # Elimina el cable de la base de datos
        messages.success(request, 'El cable ha sido eliminado correctamente.')  # Mensaje de éxito
        return redirect('cables')  # Redirige a la lista de cables
    
    return render(request, 'cables/eliminar_cable.html', {'setear_cable': setear_cable})  # Renderiza la plantilla para confirmar la eliminación

@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def cables(request):
    query = request.GET.get('q', '')  # Obtener la consulta de búsqueda desde los parámetros GET
    if query:
        setear_cables = Cables.objects.filter(
            referencia__icontains=query  # Filtrar cables que contienen la consulta en 'referencia'
        ).order_by('referencia')  # Ordenar por 'referencia'
    else:
        setear_cables = Cables.objects.all().order_by('referencia')  # Obtener todos los cables si no hay consulta

    # Identificar cables con stock bajo
    cables_bajo_stock = [cable for cable in setear_cables if cable.verificar_stock_minimo()]  # Filtrar cables con stock bajo

    # Enviar correos solo si es necesario
    for cable in cables_bajo_stock:
        if cable.necesita_advertencia():  # Verificar si se necesita advertencia
            enviar_correo_stock_bajo(cable)  # Enviar correo de advertencia
            cable.save()  # Guardar el cable actualizado

    paginator = Paginator(setear_cables, 5)  # Paginador para 5 cables por página
    page_number = request.GET.get('page', 1)  # Obtener el número de página actual
    page_obj = paginator.get_page(page_number)  # Obtener los objetos de la página actual
    
    try:
        page_obj = paginator.page(page_number)  # Obtener la página correspondiente
    except PageNotAnInteger:
        page_obj = paginator.page(1)  # Si page no es un entero, muestra la primera página
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)  # Si page está fuera de los límites, muestra la última página

    context = {
        'page_obj': page_obj,  # Paginación de cables
        'query': query,  # Mantener la consulta de búsqueda en el contexto
        'cables_bajo_stock': cables_bajo_stock,  # Pasar los cables con stock bajo al contexto
    }
    return render(request, 'cables/cables.html', context)  # Renderizar la plantilla con el contexto

def enviar_correo_stock_bajo(cable):
    # Definir el asunto del correo electrónico
    asunto = 'Advertencia: Stock Bajo de Cables'  # Asunto del correo

    # Cargar la plantilla de correo electrónico
    template = get_template('cables/correo_stock_bajo.html')  # Obtener plantilla HTML para el correo
    # Crear el contexto para la plantilla con el cable correspondiente
    context = {'cable': cable}  
    mensaje = template.render(context)  # Renderizar la plantilla con el contexto

    # Obtener todos los correos electrónicos desde la base de datos
    destinatarios = DestinatarioCorreo.objects.values_list('correo', flat=True)  # Obtener lista de correos
    remitente = 'dispensador@glingenieros.co'  # Correo del remitente
    
    # Enviar el correo electrónico
    send_mail(
        asunto,
        mensaje,
        remitente,
        destinatarios,
        fail_silently=False,  # No silenciar errores
        html_message=mensaje  # Incluir el mensaje HTML
    )

@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def crear_destinatario(request):
    if request.method == 'POST':  # Verificar si la solicitud es un POST
        form = DestinatarioCorreoForm(request.POST)  # Crear el formulario con los datos enviados
        if form.is_valid():  # Verificar si el formulario es válido
            try:
                form.save()  # Guardar el destinatario
                messages.success(request, 'Destinatario creado exitosamente.')  # Mensaje de éxito
                return redirect('lista_destinatarios')  # Redirigir a la lista de destinatarios
            except IntegrityError:  # Manejar errores de integridad
                messages.error(request, 'Error al guardar el destinatario. Verifique los datos ingresados.')  # Mensaje de error
    else:
        form = DestinatarioCorreoForm()  # Crear un formulario vacío para la solicitud GET

    return render(request, 'destinatarios/crear_destinatario.html', {'form': form})  # Renderizar la plantilla con el formulario

@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def editar_destinatario(request, id):
    destinatario = get_object_or_404(DestinatarioCorreo, id=id)  # Obtener el destinatario por ID

    if request.method == 'POST':  # Verificar si la solicitud es un POST
        form = DestinatarioCorreoForm(request.POST, instance=destinatario)  # Crear el formulario con los datos enviados
        if form.is_valid():  # Verificar si el formulario es válido
            try:
                form.save()  # Guardar el destinatario actualizado
                messages.success(request, 'Destinatario actualizado exitosamente.')  # Mensaje de éxito
                return redirect('lista_destinatarios')  # Redirigir a la lista de destinatarios
            except IntegrityError:  # Manejar errores de integridad
                messages.error(request, 'Error al actualizar el destinatario. Verifique si el correo ya existe.')  # Mensaje de error
    else:
        form = DestinatarioCorreoForm(instance=destinatario)  # Crear el formulario con los datos del destinatario existente

    return render(request, 'destinatarios/editar_destinatario.html', {'form': form})  # Renderizar la plantilla con el formulario

@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def eliminar_destinatario(request, id):
    destinatario = get_object_or_404(DestinatarioCorreo, id=id)  # Obtener el destinatario por ID

    if request.method == 'POST':  # Verificar si la solicitud es un POST
        destinatario.delete()  # Eliminar el destinatario
        messages.success(request, 'El destinatario ha sido eliminado correctamente.')  # Mensaje de éxito
        return redirect('lista_destinatarios')  # Redirigir a la lista de destinatarios

    return render(request, 'destinatarios/eliminar_destinatario.html', {'destinatario': destinatario})  # Renderizar la plantilla de confirmación

@verificar_rol('admin', 'superadmin')  # Decorador para verificar los permisos de rol
def lista_destinatarios(request):
    query = request.GET.get('q')  # Obtener la consulta de búsqueda del GET
    if query:
        destinatarios = DestinatarioCorreo.objects.filter(  # Filtrar los destinatarios según la consulta
            Q(correo__icontains=query)
        ).order_by('correo')  # Ordenar por correo
    else:
        destinatarios = DestinatarioCorreo.objects.all().order_by('correo')  # Obtener todos los destinatarios si no hay consulta
    
    paginator = Paginator(destinatarios, 5)  # Pagina los destinatarios con 5 por página
    page_number = request.GET.get('page')  # Obtener el número de página del GET

    try:
        page_obj = paginator.page(page_number)  # Obtener la página correspondiente
    except PageNotAnInteger:
        page_obj = paginator.page(1)  # Si page no es un entero, muestra la primera página
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)  # Si page está fuera de los límites, muestra la última página

    context = {
        'page_obj': page_obj,  # Pasar la página de destinatarios al contexto
        'query': query,  # Mantener la consulta de búsqueda en el contexto
    }
    return render(request, 'destinatarios/lista_destinatarios.html', context) # Renderizar la plantilla con el contexto

#Crud configurar cable, esp y encoder
@verificar_rol('admin', 'superadmin') 
def crear_configuracion_cable(request):
    if request.method == 'POST':
        form = ConfiguracionCableForm(request.POST)
        if form.is_valid():
            try:
                form.save()  # Guarda la configuración en la base de datos
                messages.success(request, 'Configuración de cable creada exitosamente.')  # Mensaje de éxito
                return redirect('listar_configuraciones_cable')  # Redirige a la lista de configuraciones después de guardar
            except IntegrityError:  # Captura errores de integridad (por ejemplo, duplicados)
                messages.error(request, 'Error al guardar la configuración. Verifica los datos ingresados.')  # Mensaje de error
    else:
        form = ConfiguracionCableForm()  # Crea un formulario vacío si no es una solicitud POST

    return render(request, 'configuracion/crear_configuracion_cable.html', {'form': form})

@verificar_rol('admin', 'superadmin')
def editar_configuracion_cable(request, id):
    configuracion = get_object_or_404(ConfiguracionCable, id=id)

    if request.method == 'POST':
        form = ConfiguracionCableForm(request.POST, instance=configuracion)
        if form.is_valid():
            try:
                form.save()  # Guarda la configuración
                messages.success(request, 'Configuración de cable actualizada exitosamente.')
                return redirect('listar_configuraciones_cable')
            except IntegrityError:
                messages.error(request, 'Error al actualizar la configuración. Verifica los datos ingresados.')
    else:
        form = ConfiguracionCableForm(instance=configuracion)  # Carga la instancia existente

    return render(request, 'configuracion/editar_configuracion_cable.html', {'form': form})

@verificar_rol('admin', 'superadmin') 
def eliminar_configuracion_cable(request, id):
    configuracion = get_object_or_404(ConfiguracionCable, id=id)
    if request.method == 'POST':
        configuracion.delete()
        messages.success(request, 'configuración de cable ha sido eliminado correctamente.')  # Mensaje de éxito
        return redirect('listar_configuraciones_cable')
    
    return render(request, 'configuracion/eliminar_configuracion_cable.html', {'configuracion': configuracion})

@verificar_rol('admin', 'superadmin') 
def listar_configuraciones_cable(request):
    query = request.GET.get('q')  # Obtener la consulta de búsqueda
    if query:
        # Filtra las configuraciones basadas en la consulta
        configuraciones = ConfiguracionCable.objects.filter(
            Q(cable__referencia__icontains=query) |
            Q(esp__icontains=query) |
            Q(encoder__icontains=query)
        ).order_by('cable__referencia')  # Ordena por la descripción del cable
    else:
        # Obtiene todas las configuraciones y las ordena
        configuraciones = ConfiguracionCable.objects.all().order_by('cable__referencia')

    paginator = Paginator(configuraciones, 5)  # Pagina las configuraciones con 5 por página
    page_number = request.GET.get('page')  # Obtener el número de página de la solicitud
    page_obj = paginator.get_page(page_number)  # Obtiene las configuraciones paginadas
    
    try:
        page_obj = paginator.page(page_number)  # Obtener la página correspondiente
    except PageNotAnInteger:
        page_obj = paginator.page(1)  # Si page no es un entero, muestra la primera página
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)  # Si page está fuera de los límites, muestra la última página

    context = {
        'page_obj': page_obj,
        'query': query,  # Mantiene la consulta de búsqueda en el contexto
    }
    return render(request, 'configuracion/listar_configuraciones_cable.html', context)

#Operario
def on_connect(client, userdata, flags, rc):
    print(f"Conectado con código {rc}")  # Imprimir el código de conexión
    client.subscribe("Prueba-DP_GL")  # Suscribirse al tópico "Prueba-DP_GL"
    client.subscribe("Prueba-DP_GL2")  # Suscribirse al tópico "Prueba-DP_GL2"

# Función al recibir un mensaje MQTT
def on_message(client, userdata, msg):
    print(f"Tópico: {msg.topic} | Mensaje: {msg.payload}")

    try:
        mensaje = msg.payload.decode('utf-8')  # Decodificar el mensaje a UTF-8
        print(f"Mensaje recibido: {mensaje}")

        if msg.topic == "Prueba-DP_GL2":
            cantidad_dispensada = float(mensaje)  # Convertir el mensaje a float
            cable_referencia = userdata.get('cable_referencia')  # Obtener referencia del cable

            if cable_referencia:
                try:
                    cable = Cables.objects.get(referencia=cable_referencia)  # Obtener el cable por referencia
                    tablero = userdata.get('tablero')  # Obtener tablero
                    proyecto = tablero.proyecto if tablero else None  # Obtener proyecto asociado

                    # Verificar que el usuario exista antes de continuar
                    if 'usuario' not in userdata:
                        print("Error: No se ha proporcionado un usuario. No se puede dispensar cable.")
                        return  # Salir de la función sin dispensar cable

                    usuario_nombre = userdata['usuario']  # Obtener nombre de usuario
                    try:
                        # Obtener la instancia del usuario
                        usuario = Usuarios.objects.get(nombre_usuario=usuario_nombre)
                    except Usuarios.DoesNotExist:
                        print(f"Error: El usuario '{usuario_nombre}' no existe. No se puede dispensar cable.")
                        return  # Salir de la función si el usuario no existe

                    # Actualizar la cantidad restante del cable
                    if cable.cantidad_restante >= cantidad_dispensada:
                        cable.cantidad_restante -= cantidad_dispensada  # Dispensar cantidad
                        cable.save()  # Guardar cambios

                        # Obtener el valor de reproceso desde userdata
                        reproceso = userdata.get('reproceso', False)  # Obtener el valor de reproceso

                        # Registrar la dispensación en la tabla RegistroDispensa
                        RegistroDispensa.objects.create(
                            cable=cable, 
                            cantidad_dispensada=cantidad_dispensada,
                            cantidad_restante_despues=cable.cantidad_restante,  # Guardar cantidad restante después de la dispensación
                            proyecto=proyecto, 
                            tablero=tablero,
                            usuario=usuario,  # Usar la instancia de usuario obtenida
                            reproceso=reproceso  # Guardar el valor de reproceso
                        )

                        # Verificar si el stock está por debajo del mínimo
                        if cable.verificar_stock_minimo():
                            enviar_correo_stock_bajo(cable)  # Enviar advertencia de stock bajo                           
                            cable.save()

                        print(f"Stock del cable {cable_referencia} actualizado. Nueva cantidad restante: {cable.cantidad_restante}")
                        
                    else:
                        print(f"Error: No hay suficiente cable para dispensar {cantidad_dispensada}.")
                    
                    # Restablecer el flag 'solicitud_en_proceso' al finalizar el proceso
                    userdata['solicitud_en_proceso'] = False

                except Cables.DoesNotExist:
                    print(f"Error: No se encontró el cable con la referencia {cable_referencia}")
            else:
                print("Error: No se proporcionó una referencia de cable para actualizar.")

    except Exception as e:
        print(f"Error al procesar el mensaje: {e}")

# Crear un cliente MQTT
cliente = mqtt.Client()
cliente.on_connect = on_connect  # Asignar la función de conexión
cliente.on_message = on_message  # Asignar la función para recibir mensajes

# Establecer userdata
cliente.user_data_set({'solicitud_en_proceso': False})

# Intentar conectar al broker MQTT
try:
    cliente.connect("broker.hivemq.com", 1883, 60)
    print("Conectado al broker MQTT.")
except Exception as e:
    print(f"Error al conectar al broker MQTT: {e}")
    exit(1)

# Mantener el cliente en funcionamiento
cliente.loop_start()

# Vista para operario
def operario(request):
    # Verificar si el usuario tiene una cédula y si su rol es 'operario'
    if not request.session.get('user_cedula') or request.session.get('user_role') != 'operario':
        # Si no está autenticado como operario, redirigir a la página de inicio de sesión
        return redirect('login')

    # Obtener el parámetro de búsqueda de la URL
    query = request.GET.get('q')
    
    if query:
        # Filtrar los proyectos que coinciden con el tipo de proyecto o el número de proyecto
        proyectos = Proyectos.objects.filter(
            Q(tipo_proyecto__icontains=query) |  # Coincide si el tipo de proyecto contiene la consulta
            Q(numero__icontains=query)            # Coincide si el número del proyecto contiene la consulta
        ).order_by('tipo_proyecto', 'numero')     # Ordenar los proyectos por tipo y número
    else:
        # Si no hay consulta de búsqueda, obtener todos los proyectos ordenados por tipo y número
        proyectos = Proyectos.objects.all().order_by('tipo_proyecto', 'numero')

    # Configurar la paginación, mostrando 5 proyectos por página
    paginator = Paginator(proyectos, 5)
    page_number = request.GET.get('page')  # Obtener el número de página de la solicitud GET
    page_obj = paginator.get_page(page_number)  # Obtener la página correspondiente de proyectos
    
    try:
        page_obj = paginator.page(page_number)  # Obtener la página correspondiente
    except PageNotAnInteger:
        page_obj = paginator.page(1)  # Si page no es un entero, muestra la primera página
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)  # Si page está fuera de los límites, muestra la última página

    # Preparar el contexto para la plantilla
    context = {
        'page_obj': page_obj,  # Pasar la página de proyectos al contexto
        'query': query,        # Pasar la consulta de búsqueda al contexto
    }
    
    # Renderizar la plantilla 'operario.html' con el contexto preparado
    return render(request, 'operario/operario.html', context)

# Vista para ver items de un proyecto
@verificar_rol('operario') # Decorador para verificar los permisos de rol
def ver_items_proyecto(request, proyecto_id):
    # Obtener el proyecto correspondiente al ID proporcionado o devolver un error 404 si no existe
    proyecto = get_object_or_404(Proyectos, proyecto=proyecto_id)
    
    # Obtener el parámetro de búsqueda de la URL, con valor por defecto como cadena vacía
    query = request.GET.get('q', '')
    
    # Filtrar los tableros que pertenecen al proyecto especificado
    tableros = Tableros.objects.filter(proyecto=proyecto)

    if query:
        # Si hay una consulta de búsqueda, filtrar los tableros por identificador que contenga la consulta
        tableros = tableros.filter(identificador=query)

    # Ordenar los tableros por identificador
    tableros = tableros.order_by('identificador')

    # Configurar la paginación, mostrando 5 tableros por página
    paginator = Paginator(tableros, 5)
    page_number = request.GET.get('page')  # Obtener el número de página de la solicitud GET
    page_obj = paginator.get_page(page_number)  # Obtener la página correspondiente de tableros
    
    try:
        page_obj = paginator.page(page_number)  # Obtener la página correspondiente
    except PageNotAnInteger:
        page_obj = paginator.page(1)  # Si page no es un entero, muestra la primera página
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)  # Si page está fuera de los límites, muestra la última página

    # Preparar el contexto para la plantilla
    context = {
        'proyecto': proyecto,  # Pasar el proyecto actual al contexto
        'page_obj': page_obj,  # Pasar la página de tableros al contexto
        'query': query,        # Pasar la consulta de búsqueda al contexto
    }
    
    # Renderizar la plantilla 'items_proyecto.html' con el contexto preparado
    return render(request, 'operario/items_proyecto.html', context)

# Vista para ver los cables de un tablero
@verificar_rol('operario')  # Decorador para verificar los permisos de rol
def ver_cables_tablero(request, tablero_id):
    tablero = get_object_or_404(Tableros, identificador=tablero_id)  # Obtener el objeto Tableros por su identificador
    proyecto = tablero.proyecto  # Obtener el proyecto asociado al tablero
    cables = Cables.objects.all()  # Inicializa una consulta para obtener todos los cables
    query = request.GET.get('q')

    if query:
        cables = cables.filter(referencia__icontains=query)  # Filtrar cables que contienen la consulta

    # Obtener las referencias de cables dispensados en el contexto del proyecto y tablero
    referencias_dispensadas = RegistroDispensa.objects.filter(
        tablero=tablero,
        proyecto=proyecto
    ).values_list('cable__referencia', flat=True).distinct()

    # Identificar cables con stock bajo
    cables_bajo_stock = [cable for cable in cables if cable.verificar_stock_minimo()]  # Filtrar cables con stock bajo

    # Crea una lista para almacenar información sobre los cables
    cables_info = []
    for cable in cables:
        cables_info.append({
            'cable': cable,
            'dispensado': cable.referencia in referencias_dispensadas,  # Verifica si la referencia del cable está en las dispensadas
        })

    # Si la solicitud es POST, significa que el operario está tratando de dispensar un cable
    if request.method == 'POST':
        
        # Verificar si ya hay una solicitud en proceso
        if cliente.user_data_get().get('solicitud_en_proceso'):
            error_message = "Ya se ha enviado una solicitud. Espera la respuesta."
            messages.error(request, error_message)  # Mensaje de error
            return render(request, 'operario/vista_espera.html', {
                'tablero_id': tablero_id,
            })

        # Obtiene la referencia del cable seleccionado por el operario
        cable_referencia = request.POST.get('cable')

        # Si hay una referencia de cable seleccionada
        if cable_referencia:
            try:
                cable = Cables.objects.get(referencia=cable_referencia)  # Intenta obtener el cable con la referencia proporcionada
                
                # Verificar si la cantidad restante es cero
                if cable.cantidad_restante == 0:
                    messages.error(request, "No se puede dispensar el cable porque su cantidad restante es cero.")
                    return render(request, 'operario/ver_cables.html', {
                        'tablero': tablero,
                        'cables': cables,
                        'proyecto_id': proyecto.proyecto,
                        'query': query,
                        'cables_bajo_stock': cables_bajo_stock,
                    })

                config = ConfiguracionCable.objects.get(cable=cable)  # Obtiene la configuración asociada al cable
                
                # Obtiene la configuración de ESP y encoder desde la configuración
                esp_seleccionado = config.esp
                encoder_seleccionado = config.encoder
                mensaje_solicitud = f"{esp_seleccionado},{encoder_seleccionado},3"

                # Obtiene el usuario autenticado a través de la cédula guardada en la sesión
                user_cedula = request.session.get('user_cedula')
                user = Usuarios.objects.get(cedula=user_cedula)

                # Captura el valor del checkbox de reproceso
                reproceso = request.POST.get(f'reproceso_{cable_referencia}') == 'on'  # True si está marcado

                # Establecer la solicitud en proceso
                cliente.user_data_set({
                    'cable_referencia': cable_referencia,
                    'solicitud_en_proceso': True,  # Marca que hay una solicitud en proceso
                    'tablero': tablero,  # Asocia el tablero seleccionado
                    'usuario': user,  # Asocia el usuario que hace la solicitud
                    'reproceso': reproceso  # Guardamos el valor del reproceso
                })
                cliente.publish("Prueba-DP_GL", mensaje_solicitud)  # Public a el mensaje en el tópico MQTT
                print(f"Solicitud enviada: {mensaje_solicitud}")

                # Redirige a la vista de espera para que el operario espere la respuesta
                return redirect('vista_espera', tablero_id=tablero_id)

            except Cables.DoesNotExist:
                error_message = "El cable seleccionado no existe."
                messages.error(request, error_message)  # Muestra mensaje de error si no se encuentra el cable
                return render(request, 'operario/ver_cables.html', {
                    'tablero': tablero,
                    'cables': cables,
                    'proyecto_id': proyecto.proyecto,
                    'query': query,
                    'cables_bajo_stock': cables_bajo_stock,
                })
            except ConfiguracionCable.DoesNotExist:
                error_message = "No hay configuración disponible para este cable."
                messages.error(request, error_message)  # Mensaje de error
                return render(request, 'operario/ver_cables.html', {
                    'tablero': tablero,
                    'cables': cables,
                    'proyecto_id': proyecto.proyecto,
                    'query': query,
                    'cables_bajo_stock': cables_bajo_stock,
                })
        else:
            error_message = "Por favor, selecciona un cable antes de proceder."
            messages.error(request, error_message)  # Mensaje de error
            return render(request, 'operario/ver_cables.html', {
                'tablero': tablero,
                'cables': cables,
                'proyecto_id': proyecto.proyecto,
                'query': query,
                'cables_bajo_stock': cables_bajo_stock,
                'referencias_dispensadas': referencias_dispensadas,
            })

    # Renderiza la vista de cables con la información y datos actuales
    return render(request, 'operario/ver_cables.html', {
        'tablero': tablero,
        'cables_info': cables_info,  # Pasa la información sobre cables y su estado de dispensado
        'cables': cables,
        'proyecto_id': proyecto.proyecto,
        'query': query,
        'referencias_dispensadas': referencias_dispensadas,  # Pasa las referencias de cables que ya han sido dispensadas
        'cables_bajo_stock': cables_bajo_stock,  # Pasar los cables con stock bajo al contexto
    })

# Función para iniciar el cliente MQTT
def iniciar_mqtt(request):
    cliente.loop_start()  # Iniciar el ciclo del cliente MQTT para manejar la conexión y los mensajes
    return render(request, 'mqtt_conectado.html')  # Renderizar la plantilla indicando que se ha conectado al MQTT

# Rol Auditor
@verificar_rol('auditor') # Decorador para verificar los permisos de rol
def auditor(request):
    # Verificar si el usuario tiene una sesión válida y un rol de auditor
    user_cedula = request.session.get('user_cedula')  # Obtener la cédula del usuario de las sesion
    user_role = request.session.get('user_role')      # Obtener el rol del usuario de session

    # Redirigir al login si la cédula no existe o el rol no es auditor
    if not user_cedula or user_role != 'auditor':
        return redirect('login')

    return render(request, 'auditor/base.html')  # Renderizar la plantilla base del auditor

@verificar_rol('auditor') # Decorador para verificar los permisos de rol
def registros(request):
    # Obtener el filtro principal de la solicitud GET, con 'proyecto' como valor por defecto
    filtro_principal = request.GET.get('filtro_principal', 'proyecto')
    # Obtener el filtro secundario de la solicitud GET
    filtro_secundario = request.GET.get('filtro_secundario')

    # Inicializar opciones secundarias como una lista vacía
    opciones_secundarias = []
    
    # Obtener las opciones para el filtro secundario según el filtro principal
    if filtro_principal == 'operario':
        # Si el filtro principal es 'operario', obtener los nombres de los operarios únicos
        opciones_secundarias = RegistroDispensa.objects.values_list('usuario__nombre_usuario', flat=True).distinct()
    elif filtro_principal == 'proyecto':
        # Si el filtro principal es 'proyecto', obtener los nombres de los proyectos únicos
        opciones_secundarias = RegistroDispensa.objects.values_list('proyecto__proyecto', flat=True).distinct()

    # Inicializar la consulta para los registros de dispensación
    registros = RegistroDispensa.objects.all()
    
    # Filtrar los registros según los filtros seleccionados
    if filtro_principal == 'operario' and filtro_secundario:
        # Si se ha seleccionado un operario específico, filtrar por ese operario
        registros = registros.filter(usuario__nombre_usuario=filtro_secundario).values(
            'proyecto__proyecto', 'tablero__identificador', 'usuario__nombre_usuario').distinct()
    elif filtro_principal == 'operario' and not filtro_secundario:
        # Si se selecciona 'operario' sin un operario específico, mostrar todos los registros
        registros = registros.values('proyecto__proyecto', 'tablero__identificador', 'usuario__nombre_usuario').distinct()
    elif filtro_principal == 'proyecto' and filtro_secundario:
        # Si se ha seleccionado un proyecto específico, filtrar por ese proyecto
        registros = registros.filter(proyecto__proyecto=filtro_secundario).distinct('proyecto__proyecto').values(
            'proyecto__proyecto', 'tablero__identificador')
    elif filtro_principal == 'proyecto' and not filtro_secundario:
        # Si se selecciona 'proyecto' sin un proyecto específico, mostrar todos los proyectos
        registros = registros.values('proyecto__proyecto').distinct()
        
    paginator = Paginator(registros, 10)  # Mostrar 10 registros por página
    page_number = request.GET.get('page')  # Obtener el número de página desde la URL
    page_obj = paginator.get_page(page_number)
    
    try:
        page_obj = paginator.page(page_number)  # Obtener la página correspondiente
    except PageNotAnInteger:
        page_obj = paginator.page(1)  # Si page no es un entero, muestra la primera página
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)  # Si page está fuera de los límites, muestra la última página

    # Calcular el total de cables dispensados filtrado por operario si corresponde
    total_cables_dispensados = []  # Inicializar la lista para el total de cables dispensados
    if filtro_principal == 'operario':
        if filtro_secundario:
            # Si se ha seleccionado un operario específico, calcular el total de cables dispensados por él
            total_cables_dispensados = RegistroDispensa.objects.filter(usuario__nombre_usuario=filtro_secundario)\
                .values('usuario__nombre_usuario', 'proyecto__proyecto', 'tablero__identificador')\
                .annotate(total_cables=Sum('cantidad_dispensada'))\
                .order_by('usuario__nombre_usuario', 'proyecto__proyecto', 'tablero__identificador')
        else:
            # Si no hay un operario específico, calcular el total de cables dispensados por todos los operarios
            total_cables_dispensados = RegistroDispensa.objects.values('usuario__nombre_usuario', 'proyecto__proyecto', 'tablero__identificador')\
                .annotate(total_cables=Sum('cantidad_dispensada'))\
                .order_by('usuario__nombre_usuario', 'proyecto__proyecto', 'tablero__identificador')
    elif filtro_principal == 'proyecto':
        # Si el filtro principal es 'proyecto', calcular el total de cables dispensados por proyecto
        total_cables_dispensados = RegistroDispensa.objects.values('proyecto__proyecto', 'tablero__identificador')\
            .annotate(total_cables=Sum('cantidad_dispensada'))\
            .order_by('proyecto__proyecto', 'tablero__identificador')

    # Preparar el contexto para pasar a la plantilla
    context = {
        'filtro_principal': filtro_principal,  # Filtro principal seleccionado
        'filtro_secundario': filtro_secundario,  # Filtro secundario seleccionado
        'opciones_secundarias': opciones_secundarias,  # Opciones para el filtro secundario
        'page_obj': page_obj,  # Paginación
        'registros': registros,  # Registros filtrados para mostrar en la plantilla
        'total_cables_dispensados': total_cables_dispensados,  # Total de cables dispensados
    }

    # Renderizar la plantilla 'auditor/registros.html' con el contexto preparado
    return render(request, 'auditor/registros.html', context)
    
@verificar_rol('auditor') # Decorador para verificar los permisos de rol
def ver_tableros_proyecto(request, proyecto):
    # Obtener los tableros del proyecto con el total de cables dispensados
    tableros = RegistroDispensa.objects.filter(proyecto__proyecto=proyecto) \
        .values('tablero__identificador') \
        .annotate(total_cables_dispensados=Sum('cantidad_dispensada'))

    # Crear el contexto para pasar a la plantilla
    context = {
        'proyecto': proyecto,
        'tableros': tableros,
    }

    return render(request, 'auditor/tableros_proyecto.html', context)

@verificar_rol('auditor')  # Decorador para verificar los permisos de rol
def ver_referencias_cables(request, proyecto, tablero):
    # Obtener las referencias de cables del tablero con la cantidad total dispensada
    referencias_cables = RegistroDispensa.objects.filter(proyecto__proyecto=proyecto, tablero__identificador=tablero) \
        .values('cable__referencia') \
        .annotate(
            total_dispensada=Sum('cantidad_dispensada', filter=Q(reproceso=False)),  # Total sin reprocesos
            total_reproceso=Sum('cantidad_dispensada', filter=Q(reproceso=True)),  # Total de reprocesos
            total=Sum('cantidad_dispensada')  # Total general
        )

    # Preparar listas para las etiquetas (referencias) y los datos (totales)
    referencias = [referencia['cable__referencia'] for referencia in referencias_cables]
    totales_dispensada = [referencia['total_dispensada'] if referencia['total_dispensada'] is not None else 0 for referencia in referencias_cables]
    totales_reproceso = [referencia['total_reproceso'] if referencia['total_reproceso'] is not None else 0 for referencia in referencias_cables]

    # Obtener el total de metros dispensados en general
    total_dispensado_general = sum(ref['total'] for ref in referencias_cables)

    # Crear el contexto para pasar a la plantilla
    context = {
        'proyecto': proyecto,
        'tablero': tablero,
        'referencias_cables': referencias_cables,
        'referencias_json': json.dumps(referencias),  # Convertir a JSON
        'totales_dispensada_json': json.dumps(totales_dispensada),  # Convertir a JSON
        'totales_reproceso_json': json.dumps(totales_reproceso),  # Convertir a JSON
        'total_dispensado_general': total_dispensado_general,  # Agregar total general al contexto
    }

    return render(request, 'auditor/referencias_cables.html', context)

@verificar_rol('auditor') # Decorador para verificar los permisos de rol
def ver_cable(request, proyecto, tablero, operario):
    # Filtrar los cables dispensados por proyecto, tablero y operario
    cables_dispensados = RegistroDispensa.objects.filter(
        proyecto__proyecto=proyecto,
        tablero__identificador=tablero,
        usuario__nombre_usuario=operario
    ).values('cable__referencia').annotate(
        total_dispensado=Sum('cantidad_dispensada', filter=Q(reproceso=False)),  # Total sin reprocesos
        total_reproceso=Sum('cantidad_dispensada', filter=Q(reproceso=True)),  # Total de reprocesos
        total=Sum('cantidad_dispensada')  # Total general
    )

    # Obtener el proyecto y tablero seleccionados
    proyecto_obj = Proyectos.objects.get(proyecto=proyecto)
    tablero_obj = Tableros.objects.get(identificador=tablero)

    # Listas para las referencias y totales para el gráfico
    referencias = [cable['cable__referencia'] for cable in cables_dispensados]
    totales = [cable['total_dispensado'] if cable['total_dispensado'] is not None else 0 for cable in cables_dispensados]
    totales_reproceso = [cable['total_reproceso'] if cable['total_reproceso'] is not None else 0 for cable in cables_dispensados]
    totales_generales = [cable['total'] if cable['total'] is not None else 0 for cable in cables_dispensados]  # Total general por cable

    # Calcular el total de cables dispensados
    total_cables_dispensados = sum(totales) + sum(totales_reproceso)  # Sumar todos los totales dispensados

    # Contexto para la plantilla
    context = {
        'cables_dispensados': cables_dispensados,
        'proyecto': proyecto_obj,
        'tablero': tablero_obj,
        'operario': operario,
        'referencias_json': json.dumps(referencias),
        'totales_json': json.dumps(totales),
        'totales_reproceso_json': json.dumps(totales_reproceso),  # Pasamos los totales de reproceso a JSON
        'total_cables_dispensados': total_cables_dispensados,
    }

    return render(request, 'auditor/ver_cable.html', context) # Renderiza la plantilla con el contexto

@verificar_rol('auditor')  # Decorador para verificar los permisos de rol
def registros_detallados(request):
    # Obtener los filtros
    operario = request.GET.get('operario', '')
    tablero = request.GET.get('tablero', '')
    reproceso = request.GET.get('reproceso', '')
    fecha = request.GET.get('fecha', '')
    proyecto = request.GET.get('proyecto', '')  # Obtener el filtro para proyecto

    # Obtener los operarios, tableros y proyectos relevantes
    operarios = RegistroDispensa.objects.values('usuario__nombre_usuario').distinct()
    tableros = RegistroDispensa.objects.values('tablero__identificador').distinct()
    proyectos = RegistroDispensa.objects.values('proyecto__proyecto').distinct()  # Proyectos disponibles

    # Filtrar registros según los filtros seleccionados
    filtros = Q()  # Creamos una consulta vacía para acumular los filtros

    if operario:
        filtros &= Q(usuario__nombre_usuario__icontains=operario)
    if tablero:
        filtros &= Q(tablero__identificador__icontains=tablero)
    if reproceso:
        filtros &= Q(reproceso=reproceso == 'True')
    if fecha:
        fecha_obj = parse_date(fecha)
        if fecha_obj:
            filtros &= Q(fecha__date=fecha_obj)
    if proyecto:
        filtros &= Q(proyecto__proyecto__icontains=proyecto)  # Filtrar por proyecto

    # Obtener los registros filtrados
    registros = RegistroDispensa.objects.filter(filtros).order_by('fecha')

    # Configurar la paginación
    paginator = Paginator(registros, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    try:
        page_obj = paginator.page(page_number)  # Obtener la página correspondiente
    except PageNotAnInteger:
        page_obj = paginator.page(1)  # Si page no es un entero, muestra la primera página
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)  # Si page está fuera de los límites, muestra la última página

    context = {
        'page_obj': page_obj,
        'operario': operario,
        'tablero': tablero,
        'reproceso': reproceso,
        'fecha': fecha,
        'proyecto': proyecto,  # Pasar el filtro de proyecto al contexto
        'operarios': operarios,
        'tableros': tableros,
        'proyectos': proyectos,  # Pasar los proyectos disponibles al contexto
        'query_params': request.GET.urlencode(),
    }
    return render(request, 'auditor/registros_detallados.html', context) # Renderiza la plantilla con el contexto

@verificar_rol('operario')
def vista_espera(request, tablero_id):
    if request.method == 'POST':
        if 'cancelar' in request.POST:
            # Cancelar solicitud actual
            cliente.user_data_set({'solicitud_en_proceso': False})
            messages.success(request, "La dispensación ha sido cancelada con éxito.")
            return redirect('ver_cables_tablero', tablero_id=tablero_id)

        # Verificar si el usuario está en proceso de dispensar
        solicitud_en_proceso = cliente.user_data_get().get('solicitud_en_proceso')
        if not solicitud_en_proceso:
            # Finalizar dispensación y pasar al siguiente en cola
           
            return redirect('operario/vista_espera')

    # Verifica si la solicitud es AJAX para actualizar estado en tiempo real
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        solicitud_en_proceso = cliente.user_data_get().get('solicitud_en_proceso')
        return JsonResponse({'solicitud_en_proceso': solicitud_en_proceso})

    return render(request, 'operario/vista_espera.html', {'tablero_id': tablero_id})
