from django.shortcuts import redirect
from functools import wraps

# Decorador para verificar el rol del usuario
def verificar_rol(*roles_permitidos):
    def decorator(view_func):
        # Utilizar el decorador wraps para preservar la metadata de la función original
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Obtener la cédula y el rol del usuario de las cookies de la solicitud
            user_cedula = request.COOKIES.get('user_cedula')
            user_role = request.COOKIES.get('user_role')
            
            # Verificar si el usuario no tiene cédula o su rol no está en la lista de roles permitidos
            if not user_cedula or user_role not in roles_permitidos:
                return redirect('login')
            
            # Si el usuario cumple con los requisitos, llamar a la función original con los argumentos proporcionados
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator