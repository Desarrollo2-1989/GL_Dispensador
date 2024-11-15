"""
URL configuration for Dispensador project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# Importa el módulo de administración de Django.
from django.contrib import admin
# Importa las funciones para definir las rutas URL.
from django.urls import path, include

# Lista de patrones de URL para el proyecto.
urlpatterns = [
    # Ruta para acceder al panel de administración de Django.
    path('admin/', admin.site.urls),
    # Ruta raíz que incluye las URL definidas en el módulo 'tasks.urls'.
    path("", include('tasks.urls')),
]