from django.shortcuts import redirect  # Importa la función redirect para redirigir usuarios
from functools import wraps  # Importa wraps para preservar metadata de funciones

# Decorador para verificar el rol del usuario
def verificar_rol(*roles_permitidos):
    def decorator(view_func):
        # Utilizar el decorador wraps para preservar la metadata de la función original
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Obtener la cédula y el rol del usuario de las cookies de la solicitud
            user_cedula = request.COOKIES.get('user_cedula')  # Obtiene la cédula del usuario desde las cookies
            user_role = request.COOKIES.get('user_role')  # Obtiene el rol del usuario desde las cookies
            
            # Verificar si el usuario no tiene cédula o su rol no está en la lista de roles permitidos
            if not user_cedula or user_role not in roles_permitidos:
                return redirect('login')  # Redirige al usuario a la página de inicio de sesión
            
            # Si el usuario cumple con los requisitos, llamar a la función original con los argumentos proporcionados
            return view_func(request, *args, **kwargs)  # Llama a la función de vista original
        return _wrapped_view  # Retorna la función envuelta
    return decorator  # Retorna el decorador
