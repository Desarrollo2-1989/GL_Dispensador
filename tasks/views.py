from urllib import request
from django.template import Context
from django.http import JsonResponse
from django.template.loader import get_template
import chardet
from django.utils import timezone 
from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Usuarios, Proyectos, Tableros, Cables, MensajePruebaDP, RegistroDispensa, DestinatarioCorreo
from .forms import  LoginForm, UsuarioForm, ProyectoForm, TablerosForm, CableForm, DestinatarioCorreoForm
from django.db import IntegrityError
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
import csv
from .decorators import verificar_rol
import io
from django.core.mail import send_mail
from django.shortcuts import render
import paho.mqtt.publish as publicar
import paho.mqtt.client as mqtt
import threading
import paho.mqtt.publish as publish
from django.http import JsonResponse
from django.db.models import Sum
import json

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            nombre_usuario = form.cleaned_data['nombre_usuario']
            contraseña = form.cleaned_data['contraseña']
            try:
                user = Usuarios.objects.get(nombre_usuario=nombre_usuario)

                # Ver ificar si el usuario está activo
                if not user.estado:
                    messages.error(request, "El usuario está inactivo.")
                    return render(request, 'login.html', {'form': form})

                # Verificar si la contraseña es correcta
                if check_password(contraseña, user.contraseña):
                    # Redireccionar basado en el rol del usuario
                    if user.rol == 'superadmin':
                        response = redirect('administrar_usuarios')
                    elif user.rol == 'admin':
                        response = redirect('administrar_usuarios')
                    elif user.rol == 'operario':
                        response = redirect('operario')
                    else:
                        response = redirect('auditor')

                    # Guardar cookies con la cédula y el rol
                    response.set_cookie('user_cedula', user.cedula)
                    response.set_cookie('user_role', user.rol)
                    response.set_cookie('user_name', user.nombre_persona)  # Guardar el nombre de la persona

                    return response
                else:
                    messages.error(request, "Contraseña incorrecta.")
            except Usuarios.DoesNotExist:
                # Mensaje cuando el usuario no existe
                messages.error(request, "El usuario no existe.")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def logout(request):
    # Crear una respuesta de redirección a la página de login
    response = redirect('login')
    # Eliminar las cookies de la sesión del usuario
    response.delete_cookie('user_cedula')
    response.delete_cookie('user_role')
    # Retornar la respuesta con las cookies eliminadas
    return response

def administrador(request):
    # Verificar si el usuario tiene una sesión válida y un rol de administrador
    if not request.COOKIES.get('user_cedula') or request.COOKIES.get('user_role') != 'admin':
        return redirect('login')
    return render(request, 'adminlte/base.html')

def superAdmin(request):
    # Verificar si el usuario tiene una sesión válida y un rol de superadministrador
    if not request.COOKIES.get('user_cedula') or request.COOKIES.get('user_role') != 'superadmin':
        return redirect('login')
    return render(request, 'adminlte/base.html')

# CRUD PARA CREAR USUARIO  
@verificar_rol('admin', 'superadmin')
def crear_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST, request=request)
        if form.is_valid():
            try:
                usuario = form.save(commit=False)
                usuario.contraseña = make_password(usuario.contraseña)

                # Verifica el rol antes de guardar
                user_role = request.COOKIES.get('user_role')
                if user_role == 'admin' and usuario.rol in ['admin', 'superadmin']:
                    messages.error(request, 'No tienes permisos para crear administradores o superadministradores.')
                    return redirect('crear_usuario')

                usuario.save()
                messages.success(request, 'Usuario creado exitosamente.')
                return redirect('administrar_usuarios')
            except IntegrityError:
                if 'nombre_usuario' in form.errors:
                    form.add_error('nombre_usuario', 'Ya existe un usuario con este nombre de usuario.')
                if 'cedula' in form.errors:
                    form.add_error('cedula', 'Ya existe un usuario con esta cédula.')
    else:
        form = UsuarioForm(request=request)

    return render(request, 'usuarios/crear_usuario.html', {'form': form})

@verificar_rol('admin', 'superadmin')
def editar_usuario(request, cedula):
    usuario = get_object_or_404(Usuarios, cedula=cedula)
    current_user_role = request.COOKIES.get('user_role')
    current_user_cedula = request.COOKIES.get('user_cedula')

    # Verifica si el usuario actual es un admin intentando editar a superadmin o a otro admin
    if current_user_role == 'admin' and (usuario.rol == 'superadmin' or usuario.rol == 'admin'):
        messages.error(request, 'No tiene permiso para editar a otro administrador o superadmin.')
        return redirect('administrar_usuarios')

    # Contar cuántos administradores activos hay
    admin_count = Usuarios.objects.filter(rol='admin', estado=True).count()

    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario, request=request)
        if form.is_valid():
            try:
                usuario = form.save(commit=False)
                
                # Cifra la contraseña solo si ha sido modificada
                if form.cleaned_data.get('contraseña'):
                    usuario.contraseña = make_password(form.cleaned_data['contraseña'])
                else:
                    # Mantiene la contraseña actual si no se proporciona una nueva
                    usuario.contraseña = Usuarios.objects.get(cedula=cedula).contraseña
                
                # Bloquear el cambio de rol si el usuario es superadmin
                if usuario.rol == 'superadmin':
                    usuario.rol = Usuarios.objects.get(cedula=cedula).rol
                
                # Asegurarse de que el estado del superadmin siempre sea activo
                if usuario.rol == 'superadmin':
                    usuario.estado = True  # Siempre activo

                # Verificar si se intenta poner inactivo a un administrador
                if usuario.rol == 'admin' and form.cleaned_data.get('estado') == False and admin_count <= 1:
                    messages.error(request, 'Debe haber al menos un administrador activo.')
                    return redirect('administrar_usuarios')

                usuario.save()
                messages.success(request, 'Usuario actualizado exitosamente')

                # Actualizar la cookie si el usuario autenticado es el mismo que el editado
                if current_user_cedula == usuario.cedula:
                    response = redirect('administrar_usuarios')
                    response.set_cookie('user_role', usuario.rol)  # Actualiza el rol en la cookie
                    response.set_cookie('user_name', usuario.nombre_persona)  # Actualiza el nombre en la cookie
                    return response
                
                return redirect('administrar_usuarios')  # Redirige a la lista de usuarios después de editar
            except IntegrityError:
                messages.error(request, 'Error al actualizar el usuario.')
    else:
        form = UsuarioForm(instance=usuario, request=request)

    return render(request, 'usuarios/editar_usuario.html', {'form': form, 'admin_count': admin_count})

@verificar_rol('admin', 'superadmin')
def eliminar_usuario(request, cedula):
    usuario = get_object_or_404(Usuarios, cedula=cedula)
    user_role = request.COOKIES.get('user_role')

    # Verificar si el usuario a eliminar es el superadmin
    if usuario.rol == 'superadmin':
        messages.error(request, 'No se puede eliminar al superadministrador.')
        return redirect('administrar_usuarios')

    # Verificar si el usuario a eliminar es un admin
    if usuario.rol == 'admin':
        # Contar cuántos administradores activos hay
        admin_count = Usuarios.objects.filter(rol='admin', estado=True).count()
        if admin_count <= 1:
            messages.error(request, 'Debe haber al menos un administrador activo.')
            return redirect('administrar_usuarios')

    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'El usuario ha sido eliminado correctamente.')
        return redirect('administrar_usuarios')

    return render(request, 'eliminar_usuario.html', {'usuario': usuario})

@verificar_rol('admin', 'superadmin')
def administrar_usuarios(request):
    query = request.GET.get('q')
    user_role = request.COOKIES.get('user_role')
    
    # Realizar la búsqueda de usuarios según la consulta y el rol del usuario
    if query:
        if user_role == 'admin':
            usuarios = Usuarios.objects.filter(
                Q(cedula__icontains=query) |
                Q(nombre_persona__icontains=query) |
                Q(nombre_usuario__icontains=query) |
                Q(rol__icontains=query),
                Q(rol='operario') | Q(rol='auditor')
            ).order_by('nombre_usuario')
        else:  # superadmin
            usuarios = Usuarios.objects.filter(
                Q(cedula__icontains=query) |
                Q(nombre_persona__icontains=query) |
                Q(nombre_usuario__icontains=query) |
                Q(rol__icontains=query),
            ).order_by('nombre_usuario')
    else:
        if user_role == 'admin':
            usuarios = Usuarios.objects.filter(
                Q(rol='operario') | Q(rol='auditor')
            ).order_by('nombre_usuario')
        else:  # superadmin
            usuarios = Usuarios.objects.all().order_by('nombre_usuario')

    paginator = Paginator(usuarios, 5)  # Mostrar 5 usuarios por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,  # Mantener la consulta de búsqueda en el contexto
    }
    return render(request, 'usuarios/administrar_usuarios.html', context)

#CRUD PROYECTO      
@verificar_rol('admin', 'superadmin')
def crear_proyecto(request):
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Proyecto creado exitosamente.')
                return redirect('manejo_proyectos')
            except IntegrityError:
                messages.error(request, 'Error al guardar el proyecto. Verifica los datos ingresados.')
    else:
        form = ProyectoForm()

    return render(request, 'proyectos/crear_proyecto.html', {'form': form})

@verificar_rol('admin', 'superadmin')
def editar_proyecto(request, proyecto):
    # Obtener el proyecto a editar desde la base de datos
    proyecto_instance = get_object_or_404(Proyectos, proyecto=proyecto)
    
    # Manejar la solicitud POST para actualizar el proyecto
    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto_instance)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Proyecto actualizado exitosamente.')
                return redirect('manejo_proyectos')
            except IntegrityError:
                messages.error(request, 'Error al actualizar el proyecto. Verifica si el proyecto ya existe.')
    else:
        form = ProyectoForm(instance=proyecto_instance)

    return render(request, 'proyectos/editar_proyecto.html', {'form': form})

@verificar_rol('admin', 'superadmin')
def eliminar_proyecto(request, proyecto):
    # Obtener el proyecto a eliminar desde la base de datos
    proyecto = get_object_or_404(Proyectos, proyecto=proyecto)
    
    # Manejar la solicitud POST para eliminar el proyecto
    if request.method == 'POST':
        proyecto.delete()
        messages.success(request, 'El proyecto ha sido eliminado correctamente.')
        return redirect('manejo_proyectos')

    return render(request, 'proyectos/eliminar_proyecto.html', {'proyecto': proyecto})

@verificar_rol('admin', 'superadmin')
def manejo_proyectos(request):
    query = request.GET.get('q')
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
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'proyectos/manejo_proyectos.html', context)

#CRUD TABLERO 
@verificar_rol('admin', 'superadmin')
def crear_tablero(request):
    if request.method == 'POST':
        form = TablerosForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, 'Tablero creado exitosamente.')
                    return redirect('tableros')
            except Exception as e:
                # Muestra un mensaje genérico si ocurre un error
                messages.error(request, 'Error al guardar el tablero. Verifique los datos ingresados.')
    else:
        form = TablerosForm()

    return render(request, 'tableros/crear_tablero.html', {'form': form})

@verificar_rol('admin', 'superadmin')
def editar_tablero(request, identificador):
    # Obtener el tablero a editar desde la base de datos
    tablero = get_object_or_404(Tableros, identificador=identificador)
    
    # Manejar la solicitud POST para actualizar el tablero
    if request.method == 'POST':
        form = TablerosForm(request.POST, instance=tablero)
        
        # Verificar si el formulario es válido
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Tablero actualizado exitosamente.')
                return redirect('tableros')
            except IntegrityError:
                form.add_error('item', 'Ya existe un tablero con este item para el proyecto seleccionado.')
    else:
        form = TablerosForm(instance=tablero)

    return render(request, 'tableros/editar_tablero.html', {'form': form})

@verificar_rol('admin', 'superadmin')
def eliminar_tablero(request, identificador):
    # Obtener el tablero a eliminar desde la base de datos
    tablero = get_object_or_404(Tableros, identificador=identificador)
    
    # Manejar la solicitud POST para eliminar el tablero
    if request.method == 'POST':
        # Eliminar el tablero
        tablero.delete()
        messages.success(request, 'El tablero ha sido eliminado correctamente.')
        return redirect('tableros')

    return render(request, 'tableros/eliminar_tablero.html', {'tablero': tablero})

@verificar_rol('admin', 'superadmin')
def tableros(request):
    query = request.GET.get('q')
    if query:
        tableros = Tableros.objects.filter(
            Q(identificador__icontains=query) 
        ).order_by('proyecto', 'item')
    else:
        tableros = Tableros.objects.all().order_by('proyecto', 'item')
    
    paginator = Paginator(tableros, 5)  # Mostrar 5 tableros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,  # Mantener la consulta de búsqueda en el contexto
    }
    return render(request, 'tableros/tableros.html', context)

@verificar_rol('admin', 'superadmin')
def cargar_csv_tableros(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        try:
            # Leer el archivo CSV en memoria
            csv_data = csv_file.read()

            # Detectar la codificación del archivo CSV
            result = chardet.detect(csv_data)
            charenc = result['encoding']

            # Decodificar el archivo CSV
            csv_data = csv_data.decode(charenc)

            # Leer los datos del archivo CSV
            reader = csv.DictReader(io.StringIO(csv_data), delimiter=';', quotechar='"', quoting=csv.QUOTE_NONE)
            
            # Listas para almacenar mensajes de éxito y de existencia
            created_messages = []
            existing_messages = []
            
            for row in reader:
                tipo_proyecto = row.get('Tipo')
                numero = row.get('Numero')
                item = row.get('Item')

                if not tipo_proyecto:
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
            if created_messages:
                messages.success(request, "Tableros creados:\n" + "\n".join(created_messages))
            if existing_messages:
                messages.info(request, "Tableros existentes:\n" + "\n".join(existing_messages))

        except Exception as e:
            messages.error(request, f'Error al cargar el archivo CSV: {e}')
            return redirect('cargar_csv')
    
    return render(request, 'tableros/cargar_csv.html')


#CRUD CABLE    
@verificar_rol('admin', 'superadmin')
def crear_cable(request):
    if request.method == 'POST':
        form = CableForm(request.POST)
        if form.is_valid():
            try:
                # Guardar el cable y establecer cantidad_restante igual a cantidad_inicial
                setear_cable = form.save(commit=False)
                setear_cable.cantidad_restante = setear_cable.cantidad_inicial
                setear_cable.save()
                messages.success(request, 'Cable creado exitosamente.')
                return redirect('cables')
            except IntegrityError:
                messages.error(request, 'Error al guardar el cable. Verifica los datos ingresados.')
    else:
        form = CableForm()
    
    return render(request, 'cables/crear_cable.html', {'form': form})

@verificar_rol('admin', 'superadmin')
def editar_cable(request, referencia):
    setear_cable = get_object_or_404(Cables, referencia=referencia)
    
    if request.method == 'POST':
        form = CableForm(request.POST, instance=setear_cable)
        if form.is_valid():
            try:
                # Actualizar el cable y mantener cantidad_restante igual a cantidad_inicial
                setear_cable = form.save(commit=False)
                setear_cable.cantidad_restante = setear_cable.cantidad_inicial
                setear_cable.save()
                messages.success(request, 'Cable actualizado exitosamente.')
                return redirect('cables')
            except IntegrityError:
                messages.error(request, 'Error al actualizar el cable. Verifica si el cable ya existe.')
    else:
        form = CableForm(instance=setear_cable)
    
    return render(request, 'cables/editar_cable.html', {'form': form})

@verificar_rol('admin', 'superadmin')
def eliminar_cable(request, referencia):
    # Obtener el cable a eliminar desde la base de datos
    setear_cable = get_object_or_404(Cables, referencia=referencia)
    
    # Manejar la solicitud POST para eliminar el cable
    if request.method == 'POST':
        setear_cable.delete()
        messages.success(request, 'El cable ha sido eliminado correctamente.')
        return redirect('cables')
    
    return render(request, 'cables/eliminar_cable.html', {'setear_cable': setear_cable})

@verificar_rol('admin', 'superadmin')
def cables(request):
    query = request.GET.get('q', '')
    if query:
        setear_cables = Cables.objects.filter(
            referencia__icontains=query
        ).order_by('referencia')
    else:
        setear_cables = Cables.objects.all().order_by('referencia')

    # Identificar cables con stock bajo
    cables_bajo_stock = [cable for cable in setear_cables if cable.verificar_stock_minimo()]

    # Enviar correos solo si es necesario
    for cable in cables_bajo_stock:
        if cable.necesita_advertencia():
            enviar_correo_stock_bajo(cable)
            cable.ultima_advertencia = timezone.now()
            cable.save()

    paginator = Paginator(setear_cables, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'cables_bajo_stock': cables_bajo_stock,
    }
    return render(request, 'cables/cables.html', context)

def enviar_correo_stock_bajo(cable):
    # Definir el asunto del correo electrónico
    asunto = 'Advertencia: Stock Bajo de Cables'

    # Cargar la plantilla de correo electrónico
    template = get_template('cables/correo_stock_bajo.html')
    # Crear el contexto para la plantilla con el cable correspondiente
    context = {'cable': cable}  
    mensaje = template.render(context)

    # Obtener todos los correos electrónicos desde la base de datos
    destinatarios = DestinatarioCorreo.objects.values_list('correo', flat=True)
    remitente = 'dispensador@glingenieros.co'
    
    # Enviar el correo electrónico
    send_mail(
        asunto,
        mensaje,
        remitente,
        destinatarios,
        fail_silently=False,
        html_message=mensaje
    )

@verificar_rol('admin', 'superadmin')
def crear_destinatario(request):
    if request.method == 'POST':
        form = DestinatarioCorreoForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Destinatario creado exitosamente.')
                return redirect('lista_destinatarios')
            except IntegrityError:
                messages.error(request, 'Error al guardar el destinatario. Verifique los datos ingresados.')
    else:
        form = DestinatarioCorreoForm()

    return render(request, 'destinatarios/crear_destinatario.html', {'form': form})

@verificar_rol('admin', 'superadmin')
def editar_destinatario(request, id):
    destinatario = get_object_or_404(DestinatarioCorreo, id=id)
    
    if request.method == 'POST':
        form = DestinatarioCorreoForm(request.POST, instance=destinatario)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Destinatario actualizado exitosamente.')
                return redirect('lista_destinatarios')
            except IntegrityError:
                messages.error(request, 'Error al actualizar el destinatario. Verifique si el correo ya existe.')
    else:
        form = DestinatarioCorreoForm(instance=destinatario)

    return render(request, 'destinatarios/editar_destinatario.html', {'form': form})

@verificar_rol('admin', 'superadmin')
def eliminar_destinatario(request, id):
    destinatario = get_object_or_404(DestinatarioCorreo, id=id)
    
    if request.method == 'POST':
        destinatario.delete()
        messages.success(request, 'El destinatario ha sido eliminado correctamente.')
        return redirect('lista_destinatarios')

    return render(request, 'destinatarios/eliminar_destinatario.html', {'destinatario': destinatario})

@verificar_rol('admin', 'superadmin')
def lista_destinatarios(request):
    query = request.GET.get('q')
    if query:
        destinatarios = DestinatarioCorreo.objects.filter(
            Q(correo__icontains=query)
        ).order_by('correo')
    else:
        destinatarios = DestinatarioCorreo.objects.all().order_by('correo')
    
    paginator = Paginator(destinatarios, 5)  # Pagina los destinatarios con 5 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'destinatarios/lista_destinatarios.html', context)

#Operario
def on_connect(client, userdata, flags, rc):
    print(f"Conectado con código {rc}")
    client.subscribe("Prueba-DP_GL")
    client.subscribe("Prueba-DP_GL2")

# Función al recibir un mensaje MQTT
def on_message(client, userdata, msg):
    print(f"Tópico: {msg.topic} | Mensaje: {msg.payload}")

    try:
        mensaje = msg.payload.decode('utf-8')
        print(f"Mensaje recibido: {mensaje}")

        if msg.topic == "Prueba-DP_GL":
            MensajePruebaDP.objects.create(mensaje=mensaje)
            print("Mensaje del primer topic insertado en la base de datos.")

        elif msg.topic == "Prueba-DP_GL2":
            cantidad_dispensada = float(mensaje)
            cable_referencia = userdata.get('cable_referencia')

            if cable_referencia:
                try:
                    cable = Cables.objects.get(referencia=cable_referencia)
                    tablero = userdata.get('tablero')
                    proyecto = tablero.proyecto if tablero else None

                    # Verificar que el usuario exista antes de continuar
                    if 'usuario' not in userdata:
                        print("Error: No se ha proporcionado un usuario. No se puede dispensar cable.")
                        return  # Salir de la función sin realizar la dispensación

                    usuario_nombre = userdata['usuario']
                    try:
                        # Obtener la instancia del usuario
                        usuario = Usuarios.objects.get(nombre_usuario=usuario_nombre)
                    except Usuarios.DoesNotExist:
                        print(f"Error: El usuario '{usuario_nombre}' no existe. No se puede dispensar cable.")
                        return  # Salir de la función si no se encuentra el usuario

                    # Actualizar la cantidad restante del cable
                    if cable.cantidad_restante >= cantidad_dispensada:
                        cable.cantidad_restante -= cantidad_dispensada
                        cable.save()

                        # Registrar la dispensación en la tabla RegistroDispensa
                        RegistroDispensa.objects.create(
                            cable=cable, 
                            cantidad_dispensada=cantidad_dispensada,
                            cantidad_restante_despues=cable.cantidad_restante,  # Guardar cantidad restante después de la dispensación
                            proyecto=proyecto, 
                            tablero=tablero,
                            usuario=usuario  # Usar la instancia de usuario obtenida
                        )

                        # Verificar si el stock está por debajo del mínimo
                        if cable.verificar_stock_minimo():
                            enviar_correo_stock_bajo(cable)
                            cable.ultima_advertencia = timezone.now()
                            cable.save()

                        print(f"Stock del cable {cable_referencia} actualizado. Nueva cantidad restante: {cable.cantidad_restante}")
                    else:
                        print(f"Error: No hay suficiente cable para dispensar {cantidad_dispensada}.")

                    # Restablecer el flag al recibir la respuesta
                    userdata['solicitud_en_proceso'] = False

                except Cables.DoesNotExist:
                    print(f"Error: No se encontró el cable con la referencia {cable_referencia}")
            else:
                print("Error: No se proporcionó una referencia de cable para actualizar.")

    except IntegrityError as e:
        print(f"Error de integridad al guardar el mensaje: {e}")
    except Exception as e:
        print(f"Error al procesar el mensaje: {e}")

# Crear un cliente MQTT
cliente = mqtt.Client()
cliente.on_connect = on_connect
cliente.on_message = on_message

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
    if not request.COOKIES.get('user_cedula') or request.COOKIES.get('user_role') != 'operario':
        return redirect('login')

    query = request.GET.get('q')
    if query:
        proyectos = Proyectos.objects.filter(
            Q(tipo_proyecto__icontains=query) |
            Q(numero__icontains=query)
        ).order_by('tipo_proyecto', 'numero')
    else:
        proyectos = Proyectos.objects.all().order_by('tipo_proyecto', 'numero')

    paginator = Paginator(proyectos, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'operario/operario.html', context)

# Vista para ver items de un proyecto
@verificar_rol('operario')
def ver_items_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(Proyectos, proyecto=proyecto_id)
    query = request.GET.get('q', '')
    tableros = Tableros.objects.filter(proyecto=proyecto)

    if query:
        tableros = tableros.filter(identificador__icontains=query)

    tableros = tableros.order_by('identificador')

    paginator = Paginator(tableros, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'proyecto': proyecto,
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'operario/items_proyecto.html', context)

# Vista para ver los cables de un tablero
@verificar_rol('operario')
def ver_cables_tablero(request, tablero_id):
    tablero = get_object_or_404(Tableros, identificador=tablero_id)
    proyecto = tablero.proyecto
    cables = Cables.objects.all()

    query = request.GET.get('q')
    if query:
        cables = cables.filter(referencia__icontains=query)

    if request.method == 'POST':
        cable_referencia = request.POST.get('cable')

        # Verificar si hay una solicitud en proceso
        if cliente.user_data_get().get('solicitud_en_proceso'):
            error_message = "Ya se ha enviado una solicitud. Espera la respuesta."
            return render(request, 'operario/ver_cables.html', {
                'tablero': tablero,
                'cables': cables,
                'proyecto_id': proyecto.proyecto,
                'query': query,
                'error_message': error_message,
            })

        if cable_referencia:
            esp_seleccionado = 1  # Lógica para seleccionar ESP
            encoder_seleccionado = 1  # Lógica para seleccionar encoder
            numero_reserva = 3  # Número de metros reservados

            mensaje_solicitud = f"{esp_seleccionado},{encoder_seleccionado},{numero_reserva}"

            # Obtener el usuario a partir de la cookie
            user_cedula = request.COOKIES.get('user_cedula')
            try:
                user = Usuarios.objects.get(cedula=user_cedula)
                # Publicar el mensaje en el tópico adecuado
                cliente.user_data_set({
                    'cable_referencia': cable_referencia,
                    'solicitud_en_proceso': True,
                    'tablero': tablero,
                    'usuario': user
                })
                cliente.publish("Prueba-DP_GL", mensaje_solicitud)
                print(f"Solicitud enviada: {mensaje_solicitud}")
            except Usuarios.DoesNotExist:
                error_message = "El usuario no existe."
                return render(request, 'operario/ver_cables.html', {
                    'tablero': tablero,
                    'cables': cables,
                    'proyecto_id': proyecto.proyecto,
                    'query': query,
                    'error_message': error_message,
                })

            return redirect('ver_cables_tablero', tablero_id=tablero_id)
        else:
            error_message = "Por favor, selecciona un cable antes de proceder."
            return render(request, 'operario/ver_cables.html', {
                'tablero': tablero,
                'cables': cables,
                'proyecto_id': proyecto.proyecto,
                'query': query,
                'error_message': error_message,
            })

    return render(request, 'operario/ver_cables.html', {
        'tablero': tablero,
        'cables': cables,
        'proyecto_id': proyecto.proyecto,
        'query': query,
    })

# Función para iniciar el cliente MQTT
def iniciar_mqtt(request):
    cliente.loop_start()
    return render(request, 'mqtt_conectado.html')

#Rol Auditor
@verificar_rol('auditor')
def auditor(request):
    # Verificar si el usuario tiene una sesión válida y un rol de auditor
    user_cedula = request.COOKIES.get('user_cedula')
    user_role = request.COOKIES.get('user_role')

    if not user_cedula or user_role != 'auditor':
        return redirect('login')

   
    return render(request, 'auditor/base.html')

@verificar_rol('auditor')
def registros(request):
    # Obtener los filtros seleccionados
    filtro_principal = request.GET.get('filtro_principal', 'proyecto')  # Establecer 'proyecto' como valor por defecto
    filtro_secundario = request.GET.get('filtro_secundario')

    # Obtener las opciones para el filtro secundario según el filtro principal
    if filtro_principal == 'operario':
        # Obtener los operarios que han dispensado cable
        opciones_secundarias = RegistroDispensa.objects.values_list('usuario__nombre_usuario', flat=True).distinct()
    elif filtro_principal == 'proyecto':
        # Obtener los proyectos donde han dispensado cable
        opciones_secundarias = RegistroDispensa.objects.values_list('proyecto__proyecto', flat=True).distinct()
    else:
        opciones_secundarias = []

    # Filtrar los registros según los filtros seleccionados
    registros = RegistroDispensa.objects.all()
    if filtro_principal == 'operario' and filtro_secundario:
        # Mostrar solo los proyectos y tableros donde el operario seleccionado ha dispensado cable
        registros = registros.filter(usuario__nombre_usuario=filtro_secundario).values('proyecto__proyecto', 'tablero__identificador', 'usuario__nombre_usuario').distinct()
    elif filtro_principal == 'operario' and not filtro_secundario:
        # Mostrar todos los proyectos y tableros donde han dispensado cable los operarios
        registros = registros.values('proyecto__proyecto', 'tablero__identificador', 'usuario__nombre_usuario').distinct()
    elif filtro_principal == 'proyecto' and filtro_secundario:
        # Mostrar solo el proyecto seleccionado
        registros = registros.filter(proyecto__proyecto=filtro_secundario).distinct('proyecto__proyecto').values('proyecto__proyecto', 'tablero__identificador')
    elif filtro_principal == 'proyecto' and not filtro_secundario:
        # Mostrar todos los proyectos donde han dispensado cable
        registros = registros.values('proyecto__proyecto').distinct()

    # Calcular el total de cables dispensados filtrado por operario si corresponde
    if filtro_principal == 'operario':
        if filtro_secundario:
            total_cables_dispensados = RegistroDispensa.objects.filter(usuario__nombre_usuario=filtro_secundario)\
                .values('usuario__nombre_usuario', 'proyecto__proyecto', 'tablero__identificador')\
                .annotate(total_cables=Sum('cantidad_dispensada'))\
                .order_by('usuario__nombre_usuario', 'proyecto__proyecto', 'tablero__identificador')
        else:
            total_cables_dispensados = RegistroDispensa.objects.values('usuario__nombre_usuario', 'proyecto__proyecto', 'tablero__identificador')\
                .annotate(total_cables=Sum('cantidad_dispensada'))\
                .order_by('usuario__nombre_usuario', 'proyecto__proyecto', 'tablero__identificador')
    elif filtro_principal == 'proyecto':
        total_cables_dispensados = RegistroDispensa.objects.values('proyecto__proyecto', 'tablero__identificador')\
            .annotate(total_cables=Sum('cantidad_dispensada'))\
            .order_by('proyecto__proyecto', 'tablero__identificador')

    context = {
        'filtro_principal': filtro_principal,
        'filtro_secundario': filtro_secundario,
        'opciones_secundarias': opciones_secundarias,
        'registros': registros,
        'total_cables_dispensados': total_cables_dispensados,
    }

    return render(request, 'auditor/registros.html', context)
    
@verificar_rol('auditor')
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

@verificar_rol('auditor')
def ver_referencias_cables(request, proyecto, tablero):
    # Obtener las referencias de cables del tablero con la cantidad total dispensada
    referencias_cables = RegistroDispensa.objects.filter(proyecto__proyecto=proyecto, tablero__identificador=tablero) \
        .values('cable__referencia') \
        .annotate(total_dispensada=Sum('cantidad_dispensada'))

    # Preparar listas para las etiquetas (referencias) y los datos (totales)
    referencias = [referencia['cable__referencia'] for referencia in referencias_cables]
    totales = [referencia['total_dispensada'] for referencia in referencias_cables]

    # Obtener el total de metros dispensados en general
    total_dispensado_general = sum(totales)

    # Crear el contexto para pasar a la plantilla
    context = {
        'proyecto': proyecto,
        'tablero': tablero,
        'referencias_cables': referencias_cables,
        'referencias_json': json.dumps(referencias),  # Convertir a JSON
        'totales_json': json.dumps(totales),  # Convertir a JSON
        'total_dispensado_general': total_dispensado_general,  # Agregar total general al contexto
    }

    return render(request, 'auditor/referencias_cables.html', context)

@verificar_rol('auditor')
def ver_cable(request, proyecto, tablero, operario):
    # Filtrar los cables dispensados por proyecto, tablero y operario
    cables_dispensados = RegistroDispensa.objects.filter(
        proyecto__proyecto=proyecto,
        tablero__identificador=tablero,
        usuario__nombre_usuario=operario
    ).values('cable__referencia').annotate(total_dispensado=Sum('cantidad_dispensada'))

    # Obtener el proyecto y tablero seleccionados
    proyecto_obj = Proyectos.objects.get(proyecto=proyecto)
    tablero_obj = Tableros.objects.get(identificador=tablero)

    # Listas para las referencias y totales para el gráfico
    referencias = [cable['cable__referencia'] for cable in cables_dispensados]
    totales = [cable['total_dispensado'] for cable in cables_dispensados]

    # Calcular el total de cables dispensados
    total_cables_dispensados = sum(totales)  # Sumar todos los totales dispensados

    # Contexto para la plantilla
    context = {
        'cables_dispensados': cables_dispensados,
        'proyecto': proyecto_obj,
        'tablero': tablero_obj,
        'operario': operario,
        'referencias_json': json.dumps(referencias),  # Pasamos los datos a JSON
        'totales_json': json.dumps(totales),  # Pasamos los datos a JSON
        'total_cables_dispensados': total_cables_dispensados,  # Total general
    }

    return render(request, 'auditor/ver_cable.html', context)

@verificar_rol('auditor')
def registros_detallados(request):
    # Obtener la consulta del buscador, inicializando en vacío si no hay
    query = request.GET.get('q', '')  # Cambiado aquí para asegurar que sea vacío por defecto
    
    # Filtrar registros según la consulta del buscador
    if query:
        registros = RegistroDispensa.objects.filter(
            Q(usuario__nombre_usuario__icontains=query) | 
            Q(tablero__identificador__icontains=query) 
        ).order_by('fecha')
    else:
        registros = RegistroDispensa.objects.all().order_by('fecha')

    context = {
        'registros': registros,
        'query': query,
    }
    return render(request, 'auditor/registros_detallados.html', context)














