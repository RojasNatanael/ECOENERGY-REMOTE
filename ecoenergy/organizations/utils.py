from .models import Usuario

def get_user_organization(user):
    if hasattr(user, 'usuario'):
        return user.usuario.organization
    return None

def get_user_organizations(user):

#======SI ES ENCARGADO PUEDE VER TODAS LAS ORGANIZACIONES======#
    if user.groups.filter(name='Encargado EcoEnergy').exists():
        from .models import Organization
        return Organization.objects.all()
    elif hasattr(user, 'usuario'):
#======A LOS DEMAS SOLO SE LES DEVUELVE SU ORGANIZACION======#
        return [user.usuario.organization]
    return []


def can_edit_organization(user, organization):
#======ENCARGADO PUEDE EDITAR======#
    if user.groups.filter(name='Encargado EcoEnergy').exists():
        return True
    elif hasattr(user, 'usuario'):
#======SOLO PUEDE EDITAR SI ES DE LA MISMA ORG======#
        return user.usuario.organization == organization
    return False

def filter_by_organization(user, queryset):
    """Filter queryset based on user's organization permissions"""
    if user.groups.filter(name='Encargado EcoEnergy').exists():
        # Encargado sees everything
        return queryset
    elif hasattr(user, 'usuario'):
        # Others see only their organization
        return queryset.filter(organization=user.usuario.organization)
    return queryset.none()