from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from .utils import can_edit_organization
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

def organization_required(view_func):
#======PUEDE ACCEDER SOLO SI CAN_EDIT_ORGANIZATION ES TRUE======#
    def wrapper(request, *args, **kwargs):
        from .models import Organization
        organization_id = kwargs.get('organization_id')
        if organization_id:
            organization = get_object_or_404(Organization, id=organization_id)
            if not can_edit_organization(request.user, organization):
                return HttpResponseForbidden("No tienes permisos para esta organización")
        return view_func(request, *args, **kwargs)
    return wrapper

#======SOLO PUEDE ACCEDER SI GRUPO ES ENCARGADO ECOENERGY O CLIENTE ADMIN======#
def cliente_admin(error_message="No tienes permisos para realizar esta acción."):
    
    def cliente_admin(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('dashboard')
                
            print(f"DEBUG: User groups: {list(request.user.groups.all())}")
            
            if not request.user.groups.filter(name__in=['Encargado EcoEnergy', 'Cliente Admin']).exists():
                messages.error(request, error_message)
                return redirect('dashboard')
                
            print("DEBUG: User IS Encargado - proceeding")
            return view_func(request, *args, **kwargs)
        return wrapper
    return cliente_admin

#======SOLO PUEDE ACCEDER SI GRUPO ES ENCARGADO ECOENERGY======#
def encargado(error_message="No tienes permisos para realizar esta acción."):
    
    def encargado(view_func):
        
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            
            if not request.user.is_authenticated:
                return redirect('login')
            
            if not request.user.groups.filter(name='Encargado EcoEnergy').exists():
                messages.error(request, error_message)
                return redirect('dashboard')
                
            return view_func(request, *args, **kwargs)
        return wrapper
    return encargado