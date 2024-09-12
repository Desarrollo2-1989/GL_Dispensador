from django.template import Context
from django.template.loader import get_template
import chardet
from django.utils import timezone 
from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Usuarios, Proyectos, Tableros, Cables
from .forms import  LoginForm, UsuarioForm, ProyectoForm, TablerosForm, CableForm
from django.db import IntegrityError
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
import csv
from django.contrib.auth.decorators import login_required
from .decorators import verificar_rol
import io
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            nombre_usuario = form.cleaned_data['nombre_usuario']
            contraseña = form.cleaned_data['contraseña']
            try:
                user = Usuarios.objects.get(nombre_usuario=nombre_usuario)
                
                # Verificar si la contraseña es correcta
                if check_password(contraseña, user.contraseña):
                    # Redireccionar basado en el rol del usuario
                    if user.rol == 'superadmin':
                        response = redirect('superAdmin')
                    elif user.rol == 'admin':
                        response = redirect('administrador')
                    elif user.rol == 'operario':
                        response = redirect('operario')
                    else:
                        response = redirect('auditor')
                    
                    # Guardar cookies con la cédula y el rol
                    response.set_cookie('user_cedula', user.cedula)
                    response.set_cookie('user_role', user.rol)
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
    response = redirect('login')
    response.delete_cookie('user_cedula')
    response.delete_cookie('user_role')
    return response

def administrador(request):
    if not request.COOKIES.get('user_cedula') or request.COOKIES.get('user_role') != 'admin':
        return redirect('login')
    return render(request, 'adminlte/base.html')

def auditor(request):
    if not request.COOKIES.get('user_cedula') or request.COOKIES.get('user_role') != 'auditor':
        return redirect('login')
    return render(request, 'auditor.html')

def superAdmin(request):
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

    # Verifica si el usuario actual es un admin intentando editar a superadmin
    if current_user_role == 'admin' and (usuario.rol == 'superadmin' or usuario.rol == 'admin'):
        messages.error(request, 'No tiene permiso para editar a otro administrador o superadmin.')
        return redirect('administrar_usuarios')

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
                
                usuario.save()
                messages.success(request, 'Usuario actualizado exitosamente')

                # Actualizar la cookie si el usuario autenticado es el mismo que el editado
                if current_user_cedula == usuario.cedula:
                    response = redirect('administrar_usuarios')
                    response.set_cookie('user_role', usuario.rol)  # Actualiza el rol en la cookie
                    return response
                
                return redirect('administrar_usuarios')  # Redirige a la lista de usuarios después de editar
            except IntegrityError:
                messages.error(request, 'Error al actualizar el usuario.')
    else:
        form = UsuarioForm(instance=usuario, request=request)

    return render(request, 'usuarios/editar_usuario.html', {'form': form})

@verificar_rol('admin', 'superadmin')
def eliminar_usuario(request, cedula):
    usuario = get_object_or_404(Usuarios, cedula=cedula)
    user_role = request.COOKIES.get('user_role')

    # Verificar si el usuario a eliminar es el superadmin o si el usuario autenticado es admin y está intentando eliminar otro admin
    if usuario.rol == 'superadmin':
        messages.error(request, 'No se puede eliminar al superadministrador.')
        return redirect('administrar_usuarios')
    
    if user_role == 'admin' and usuario.rol == 'admin':
        messages.error(request, 'No se puede eliminar a otro administrador desde una sesión de administrador.')
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
    proyecto_instance = get_object_or_404(Proyectos, proyecto=proyecto)
    
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
    proyecto = get_object_or_404(Proyectos, proyecto=proyecto)
    
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
    tablero = get_object_or_404(Tableros, identificador=identificador)
    
    if request.method == 'POST':
        form = TablerosForm(request.POST, instance=tablero)
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
    tablero = get_object_or_404(Tableros, identificador=identificador)
    
    if request.method == 'POST':
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
    setear_cable = get_object_or_404(Cables, referencia=referencia)
    
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

@verificar_rol('admin', 'superadmin')
def enviar_correo_stock_bajo(cable):
    asunto = 'Advertencia: Stock Bajo de Cables'
    
    template = get_template('cables/correo_stock_bajo.html')
    context = {'cable': cable}  
    mensaje = template.render(context)
    
    destinatarios = ['practicante.sistemas@glingenieros.co']
    remitente = 'dispensador@glingenieros.co'

    send_mail(
        asunto,
        mensaje,
        remitente,
        destinatarios,
        fail_silently=False,
        html_message=mensaje
    )

#Operario
def operario(request):
    if not request.COOKIES.get('user_cedula') or request.COOKIES.get('user_role') != 'operario':
        return redirect('login')

    # Obtener la consulta de búsqueda si existe
    query = request.GET.get('q')
    if query:
        proyectos = Proyectos.objects.filter(
            Q(tipo_proyecto__icontains=query) |
            Q(numero__icontains=query)
        ).order_by('tipo_proyecto', 'numero')
    else:
        proyectos = Proyectos.objects.all().order_by('tipo_proyecto', 'numero')

    # Configurar la paginación
    paginator = Paginator(proyectos, 5)  # Mostrar 10 proyectos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pasar contexto al template
    context = {
        'page_obj': page_obj,    # Para la paginación
        'query': query,          # Mantener la consulta de búsqueda en el contexto
    }
    return render(request, 'operario/operario.html', context)

@verificar_rol('operario')
def ver_items_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(Proyectos, proyecto=proyecto_id)
    # Obtener el parámetro de búsqueda
    query = request.GET.get('q', '')
    # Filtrar los tableros asociados con el proyecto
    tableros = Tableros.objects.filter(proyecto=proyecto)
    # Aplicar filtro de búsqueda si se ha proporcionado
    if query:
        tableros = tableros.filter(identificador__icontains=query)
    # Configurar la paginación
    paginator = Paginator(tableros, 5)  # Mostrar 10 tableros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Pasar contexto al template
    context = {
        'proyecto': proyecto,
        'page_obj': page_obj,  # Para la paginación
        'query': query,        # Mantener la consulta de búsqueda en el contexto
    }
    return render(request, 'operario/items_proyecto.html', context)

@verificar_rol('operario')
def ver_cables_tablero(request, tablero_id):
    # Obtener el tablero seleccionado
    tablero = get_object_or_404(Tableros, identificador=tablero_id)
    # Obtener el proyecto asociado con el tablero
    proyecto = tablero.proyecto
    # Inicializar el queryset para todos los cables
    cables = Cables.objects.all()
    # Verificar si hay una consulta de búsqueda
    query = request.GET.get('q')
    if query:
        # Filtrar cables por referencia que coincidan con la consulta
        cables = cables.filter(referencia__icontains=query)
    
    if request.method == 'POST':
        # Obtener el cable seleccionado por el usuario
        selected_cable = request.POST.get('cable')
        
        if selected_cable:
            # Obtener el objeto del cable seleccionado
            cable = get_object_or_404(Cables, referencia=selected_cable)
            # Redirigir a otra vista o mostrar un mensaje de confirmación
            return redirect('some_view')  # Cambia 'some_view' por la vista adecuada

    # Renderizar la plantilla con la lista de cables filtrada si hay búsqueda
    return render(request, 'operario/ver_cables.html', {
        'tablero': tablero,
        'cables': cables,
        'proyecto_id': proyecto.proyecto,
        'query': query,  # Pasar la consulta de búsqueda al contexto para mantenerla en el formulario
    })
