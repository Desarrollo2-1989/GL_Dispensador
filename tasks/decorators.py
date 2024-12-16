from django.shortcuts import redirect  # Importa la función redirect para redirigir usuarios
from functools import wraps  # Importa wraps para preservar metadata de funciones

# Decorador para verificar el rol del usuario
def verificar_rol(*roles_permitidos):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_cedula = request.session.get('user_cedula')
            user_role = request.session.get('user_role')

            if not user_cedula or user_role not in roles_permitidos:
                return redirect('login')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator