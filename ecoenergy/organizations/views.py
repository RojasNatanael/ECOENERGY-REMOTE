from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileForm, AdminUserProfileForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Usuario
from django.http import Http404
from .decorators import encargado, cliente_admin
from .utils import filter_by_organization
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST


@login_required
@encargado()
def register(request):

    #======SOLO ENCARGADO PUEDE REGISTRAR USUARIOS=====#

    #======RECIBE DATOS FORMULARIO POR BOTON POST======#
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)

    #======VALIDACIONES FORMULARIO======#
        if form.is_valid():

    #======GUARDAR USUARIO EN BASE DE DATOS======#
            user = form.save()
            messages.success(request, f'Usuario {form.cleaned_data.get("name")} creado exitosamente!')
            return redirect('register')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                field_name = form.fields[field].label if field in form.fields else field
                for error in errors:
                    error_messages.append(f"{field_name}: {error}")
            
            # Join all errors into one SweetAlert message
            if error_messages:
                full_error_message = "\\n• " + "\\n• ".join(error_messages)
                messages.error(request, f"Errores en el formulario:{full_error_message}")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': form})


@login_required
def profile(request):

    #======RECIBE DATOS FORMULARIO POR BOTON POST======#
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user, user=request.user)
    #======VALIDACIONES FORMULARIO======#
        if form.is_valid():
    #======GUARDAR USUARIO EN BASE DE DATOS======#
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('profile')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = UserProfileForm(instance=request.user, user=request.user)
    
    return render(request, 'profile.html', {'form': form})







def errors(request, exception=None):
    """
    Handle all error pages with a custom template
    """
    # Determine error code based on exception type
    if isinstance(exception, Http404):
        error_code = 404
        error_title = "Página No Encontrada"
        error_message = "La página que estás buscando no existe o ha sido movida."
    elif isinstance(exception, PermissionDenied):
        error_code = 403
        error_title = "Acceso Denegado"
        error_message = "No tienes permisos para acceder a esta página."
    else:
        error_code = 500
        error_title = "Error del Servidor" 
        error_message = "Ha ocurrido un error interno. Por favor, intenta más tarde."
    
    return render(request, 'error.html', {
        'error_code': error_code,
        'error_title': error_title,
        'error_message': error_message
    }, status=error_code)



@login_required
def usuario_list(request):
    # ==== GET SEARCH PARAMETERS ====
    q = (request.GET.get("q") or "").strip()
    
    # ==== GET PAGINATION SIZE (SESSION ONLY) ====
    if request.method == 'POST' and 'items_per_page' in request.POST:
        # Update session when form is submitted
        items_per_page = int(request.POST.get('items_per_page'))
        request.session['usuario_items_per_page'] = items_per_page
    else:
        # Get from session or default to 10
        items_per_page = request.session.get('usuario_items_per_page', 10)
    
    # ==== GET SORTING PARAMETERS ====
    sort_field = request.GET.get('sort', 'name')
    sort_direction = request.GET.get('direction', 'asc')
    
    # ==== BASE QUERYSET WITH ORGANIZATION FILTER ====
    qs = Usuario.objects.select_related("user", "organization")
    
    # Apply organization filter based on user role
    if request.user.groups.filter(name='Encargado EcoEnergy').exists():
        # Encargado sees ALL organizations
        pass
    elif hasattr(request.user, 'usuario'):
        # Others see only their organization
        qs = qs.filter(organization=request.user.usuario.organization)
    else:
        qs = qs.none()
    
    # ==== APPLY SEARCH FILTER ====
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(user__username__icontains=q) |
            Q(user__email__icontains=q) |
            Q(phone__icontains=q) |
            Q(organization__name__icontains=q)
        )
    
    # ==== APPLY SORTING ====
    sort_mapping = {
        'name': 'name',
        'username': 'user__username',
        'email': 'user__email', 
        'phone': 'phone',
        'organization': 'organization__name',
        'active': 'user__is_active'
    }
    
    actual_sort_field = sort_mapping.get(sort_field, 'name')
    
    # Apply sorting direction
    if sort_direction == 'desc':
        actual_sort_field = f'-{actual_sort_field}'
    
    qs = qs.order_by(actual_sort_field)
    
    # ==== PAGINATION ====
    paginator = Paginator(qs, items_per_page)
    page_number = request.GET.get("page")
    
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    
    # ==== PRESERVE PARAMETERS ====
    params = request.GET.copy()
    params.pop("page", None)
    querystring = params.urlencode()
    
    # ==== RENDER TEMPLATE ====
    return render(request, "lista_usuarios.html", {
        "page_obj": page_obj,
        "q": q,
        "querystring": querystring,
        "total": qs.count(),
        "items_per_page": items_per_page,
        "sort_field": sort_field,
        "sort_direction": sort_direction,
        "user_role": get_user_role(request.user),
    })

# Helper function to get user role
def get_user_role(user):
    if user.groups.filter(name='Encargado EcoEnergy').exists():
        return "Encargado EcoEnergy"
    elif user.groups.filter(name='Cliente Admin').exists():
        return "Cliente Admin"
    elif user.groups.filter(name='Cliente Electrónico').exists():
        return "Cliente Electrónico"
    return "Sin rol"




@login_required
@encargado()
def editar_perfil(request, user_id):
    """
    Admin version of profile editing for any user
    """
    # Get the target user (the one being edited)
    target_user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        form = AdminUserProfileForm(request.POST, request.FILES, instance=target_user, target_user=target_user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Perfil de {target_user.usuario.name} actualizado correctamente.')
            return redirect('lista_usuarios')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = AdminUserProfileForm(instance=target_user, target_user=target_user)
    
    return render(request, 'editar_perfil.html', {
        'form': form,
        'target_user': target_user
    })
@login_required
@encargado()
@require_POST
def eliminar_usuario(request, pk):
    # Get usuario based on user role
    if request.user.groups.filter(name='Encargado EcoEnergy').exists():
        # Encargado can delete any usuario
        usuario = get_object_or_404(Usuario, user__id=pk)
    elif hasattr(request.user, 'usuario'):
        # Others can only delete usuarios from their organization
        organization = request.user.usuario.organization
        usuario = get_object_or_404(Usuario, user__id=pk, organization=organization)
    else:
        return JsonResponse({
            'success': False,
            'message': '❌ No tienes permisos para eliminar usuarios.'
        })
    
    try:
        # Soft delete - deactivate the user
        usuario.user.is_active = False
        usuario.user.save()
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Usuario "{usuario.name}" eliminado exitosamente.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'❌ Error al eliminar el usuario: {str(e)}'
        })