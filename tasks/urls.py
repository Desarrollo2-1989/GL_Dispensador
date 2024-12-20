from django.urls import path
from . import views
from .views import (
    login, administrador, operario, auditor, superAdmin,
    administrar_usuarios, crear_usuario, editar_usuario, eliminar_usuario,
    manejo_proyectos, crear_proyecto, editar_proyecto, eliminar_proyecto,
    tableros, crear_tablero, editar_tablero, eliminar_tablero, cargar_csv_tableros,
    cables, crear_cable, editar_cable, eliminar_cable, reabastecer_cable,
    operario, ver_items_proyecto, ver_cables_tablero,
)

# Definición de las URL para las vistas del proyecto
urlpatterns = [
    # Ruta para la página de inicio de sesión
    path('', views.login, name='login'),
    
    # Ruta para cerrar sesión
    path('logout/', views.logout, name='logout'),
    
    # Rutas para las vistas basadas en el rol del usuario
    path('administrador/', views.administrador, name='administrador'),
    path('operario/', views.operario, name='operario'),
    path('auditor/', views.auditor, name='auditor'),
    path('superAdmin/', views.superAdmin, name='superAdmin'),
    
    
    # Rutas usuarios
    path('crear_usuario/', views.crear_usuario, name='crear_usuario'),
    path('editar_usuario/<str:cedula>/', views.editar_usuario, name='editar_usuario'),
    path('eliminar_usuario/<str:cedula>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('administrar_usuarios/', views.administrar_usuarios, name='administrar_usuarios'),
    
    # Rutas para proyectos
    path('manejo_proyectos/', views.manejo_proyectos, name='manejo_proyectos'),
    path('crear_proyecto/', views.crear_proyecto, name='crear_proyecto'),
    path('editar_proyecto/<str:proyecto>/', views.editar_proyecto, name='editar_proyecto'),
    path('eliminar_proyecto/<str:proyecto>/', views.eliminar_proyecto, name='eliminar_proyecto'),
    
    #Rutas para tableros
    path('tableros/', views.tableros, name='tableros'),
    path('crear_tablero/', views.crear_tablero, name='crear_tablero'),
    path('editar_tablero/<str:identificador>/', views.editar_tablero, name='editar_tablero'),
    path('eliminar_tablero/<str:identificador>/', views.eliminar_tablero, name='eliminar_tablero'),
    path('tableros/cargar-csv/', views.cargar_csv_tableros, name='cargar_csv'),
    
    # Rutas para cables
    path('cables/', views.cables, name='cables'),
    path('crear_cable/', views.crear_cable, name='crear_cable'),
    path('editar_cable/<str:referencia>/', views.editar_cable, name='editar_cable'),
    path('reabastecer_cable/<str:referencia>/', views.reabastecer_cable, name='reabastecer_cable'),
    path('eliminar_cable/<str:referencia>/', views.eliminar_cable, name='eliminar_cable'),
 
    
    # Rutas para operario
    path('ver_items_proyecto/<str:proyecto_id>/', views.ver_items_proyecto, name='ver_items_proyecto'),
    path('tableros/<str:tablero_id>/cables/', views.ver_cables_tablero, name='ver_cables_tablero'),
    
    #Ruta para inciar mqtt
    path('iniciar-mqtt/', views.iniciar_mqtt, name='iniciar_mqtt'),
    
    #Rutas para correo 
    path('crear_destinatario/', views.crear_destinatario, name='crear_destinatario'),
    path('editar_destinatario/<int:id>/', views.editar_destinatario, name='editar_destinatario'),
    path('eliminar_destinatario/<int:id>/', views.eliminar_destinatario, name='eliminar_destinatario'),
    path('lista_destinatarios/', views.lista_destinatarios, name='lista_destinatarios'),
      
    #Rutas para auditor
    path('registros_detallados/', views.registros_detallados, name='registros_detallados'),
    path('registros/', views.registros, name='registros'),
    path('ver_cable/<str:proyecto>/<str:tablero>/<str:operario>/', views.ver_cable, name='ver_cable'),
    path('ver_tableros_proyecto/<str:proyecto>/', views.ver_tableros_proyecto, name='ver_tableros_proyecto'),
    path('ver_referencias_cables/<str:proyecto>/<str:tablero>/', views.ver_referencias_cables, name='ver_referencias_cables'),
    
    path('configuracion/crear/', views.crear_configuracion_cable, name='crear_configuracion_cable'),
    path('configuracion/', views.listar_configuraciones_cable, name='listar_configuraciones_cable'),
    path('configuracion/editar/<int:id>/', views.editar_configuracion_cable, name='editar_configuracion_cable'),
    path('configuracion/eliminar/<int:id>/', views.eliminar_configuracion_cable, name='eliminar_configuracion_cable'),
    
    path('vista_espera/<str:tablero_id>/', views.vista_espera, name='vista_espera'),

]
