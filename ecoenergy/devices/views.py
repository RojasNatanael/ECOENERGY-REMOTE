# devices/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from organizations.models import Organization, Usuario
from .models import Product, Device, Zone, Measurement, Category
from .forms import ProductForm, DeviceForm, ZoneForm
from django.views.generic import ListView
from organizations.decorators import encargado, cliente_admin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
@login_required
def dashboard(request):
    user = request.user
    context = {}
    
    # Get user organization
    try:
        user_profile = user.usuario
        user_organization = user_profile.organization
    except Usuario.DoesNotExist:
        user_organization = None
    
    # Basic user info
    context['user_organization'] = user_organization
    context['user_role'] = get_user_role(user)
    
    # Simple stats that work with current models
    if user.groups.filter(name='Encargado EcoEnergy').exists():
        # System admin - show everything
        context['total_organizations'] = Organization.objects.count()
        context['total_users'] = Usuario.objects.count()
        context['total_zones'] = Zone.objects.count()
        context['total_devices'] = Device.objects.count()
        context['total_products'] = Product.objects.count()
        
    elif user.groups.filter(name='Cliente Admin').exists() and user_organization:
        # Organization admin - show org-specific data
        context['organization_zones'] = Zone.objects.filter(organization=user_organization).count()
        context['organization_devices'] = Device.objects.filter(organization=user_organization).count()
        context['active_devices'] = Device.objects.filter(organization=user_organization, status="ACTIVE").count()
        
    elif user.groups.filter(name='Cliente Electrónico').exists() and user_organization:
        # Read-only user - basic info
        context['total_devices'] = Device.objects.filter(organization=user_organization, status="ACTIVE").count()
        context['recent_measurements'] = Measurement.objects.filter(
            device__organization=user_organization
        ).select_related('device')[:5]
    
    return render(request, 'dashboard.html', context)

def get_user_role(user):
    if user.groups.filter(name='Encargado EcoEnergy').exists():
        return "Encargado EcoEnergy"
    elif user.groups.filter(name='Cliente Admin').exists():
        return "Cliente Admin"
    elif user.groups.filter(name='Cliente Electrónico').exists():
        return "Cliente Electrónico"
    return "Usuario"

def get_user_organization(user):
    """Get user's organization - consistent with dashboard approach"""
    try:
        user_profile = user.usuario
        return user_profile.organization
    except Usuario.DoesNotExist:
        return None



@login_required
def lista_productos(request):
    print(f"=== DEBUG PRODUCTOS VIEW ===")
    print(f"User: {request.user.username}")
    print(f"Groups: {[g.name for g in request.user.groups.all()]}")
    
    # ==== BASE QUERYSET ====
    qs = Product.objects.select_related("category").filter(status='ACTIVE')
    print(f"Total products in DB: {Product.objects.count()}")
    print(f"Active products: {qs.count()}")
    
    # Check if there are any products at all
    all_products = Product.objects.all()
    print(f"All products (including inactive): {all_products.count()}")
    for product in all_products:
        print(f" - {product.name} (status: {product.status})")
    
    # ==== GET SEARCH PARAMETERS ====
    q = (request.GET.get("q") or "").strip()
    print(f"Search query: '{q}'")
    
    # ==== APPLY SEARCH FILTER ====
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(sku__icontains=q) |
            Q(manufacturer__icontains=q) |
            Q(model_name__icontains=q) |
            Q(category__name__icontains=q)
        )
        print(f"Products after search: {qs.count()}")
    
    # ==== GET SORTING PARAMETERS ====
    sort_field = request.GET.get('sort', 'name')
    sort_direction = request.GET.get('direction', 'asc')
    print(f"Sort field: {sort_field}, direction: {sort_direction}")
    
    # ==== APPLY SORTING ====
    sort_mapping = {
        'name': 'name',
        'sku': 'sku',
        'manufacturer': 'manufacturer',
        'category': 'category__name',
        'created_at': 'created_at'
    }
    
    actual_sort_field = sort_mapping.get(sort_field, 'name')
    if sort_direction == 'desc':
        actual_sort_field = f'-{actual_sort_field}'
    
    qs = qs.order_by(actual_sort_field)
    print(f"Final queryset count: {qs.count()}")
    
    # ==== PAGINATION ====
    items_per_page = request.session.get('producto_items_per_page', 10)
    paginator = Paginator(qs, items_per_page)
    page_number = request.GET.get("page")
    
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    
    print(f"Page object has {len(page_obj)} items")
    print("=== END DEBUG ===")
    
    # ==== PRESERVE PARAMETERS ====
    params = request.GET.copy()
    params.pop("page", None)
    querystring = params.urlencode()
    
    return render(request, "productos/lista_productos.html", {
        "page_obj": page_obj,
        "q": q,
        "querystring": querystring,
        "total": qs.count(),
        "items_per_page": items_per_page,
        "sort_field": sort_field,
        "sort_direction": sort_direction,
    })

@login_required
@cliente_admin()
def lista_dispositivos(request):
    # ==== GET SEARCH PARAMETERS ====
    q = (request.GET.get("q") or "").strip()
    
    # ==== GET PAGINATION SIZE ====
    if request.method == 'POST' and 'items_per_page' in request.POST:
        items_per_page = int(request.POST.get('items_per_page'))
        request.session['dispositivo_items_per_page'] = items_per_page
    else:
        items_per_page = request.session.get('dispositivo_items_per_page', 10)
    
    # ==== GET SORTING PARAMETERS ====
    sort_field = request.GET.get('sort', 'name')
    sort_direction = request.GET.get('direction', 'asc')
    
    # ==== BASE QUERYSET ====
    qs = Device.objects.select_related("organization", "zone", "product").filter(status='ACTIVE')
    
    # ==== ORGANIZATION FILTERING BASED ON USER ROLE ====
    if request.user.groups.filter(name='Encargado EcoEnergy').exists():
        # Encargado sees ALL organizations - no filter applied
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
            Q(serial_number__icontains=q) |
            Q(product__name__icontains=q) |
            Q(zone__name__icontains=q)
        )
    
    # ==== APPLY SORTING ====
    sort_mapping = {
        'name': 'name',
        'serial_number': 'serial_number',
        'product': 'product__name',
        'zone': 'zone__name',
        'max_power': 'max_power_w',
        'created_at': 'created_at'
    }
    
    actual_sort_field = sort_mapping.get(sort_field, 'name')
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
    
    # Get current user's organization for display
    current_org = None
    if hasattr(request.user, 'usuario'):
        current_org = request.user.usuario.organization
    
    return render(request, "dispositivos/lista_dispositivos.html", {
        "page_obj": page_obj,
        "q": q,
        "querystring": querystring,
        "total": qs.count(),
        "items_per_page": items_per_page,
        "sort_field": sort_field,
        "sort_direction": sort_direction,
        "organization": current_org,
        "is_encargado": request.user.groups.filter(name='Encargado EcoEnergy').exists(),
    })


@login_required
@encargado()
def editar_producto(request, pk):
    """Edit an existing product"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'✅ Producto "{product.name}" actualizado exitosamente!')
            return redirect('lista_productos')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                field_name = form.fields[field].label if field in form.fields else field
                for error in errors:
                    error_messages.append(f"{field_name}: {error}")
            
            if error_messages:
                full_error_message = "\\n• " + "\\n• ".join(error_messages)
                messages.error(request, f"Errores en el formulario:{full_error_message}")
    else:
        form = ProductForm(instance=product)
    
    return render(request, "productos/editar_producto.html", {
        "form": form,
        "product": product,
        "title": "Editar Producto"
    })

@login_required
@encargado()
def crear_producto(request):
    """Create a new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'✅ Producto "{product.name}" creado exitosamente!')
            return redirect('lista_productos')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                field_name = form.fields[field].label if field in form.fields else field
                for error in errors:
                    error_messages.append(f"{field_name}: {error}")
            
            # Join all errors into one SweetAlert message (same as your pattern)
            if error_messages:
                full_error_message = "\\n• " + "\\n• ".join(error_messages)
                messages.error(request, f"Errores en el formulario:{full_error_message}")
    else:
        form = ProductForm()
    
    return render(request, "productos/editar_producto.html", {
        "form": form,
        "title": "Crear Producto"
    })

@login_required
@encargado()
@require_POST
def eliminar_producto(request, pk):
    """Delete product via AJAX (soft delete)"""
    product = get_object_or_404(Product, pk=pk)
    
    try:
        # Soft delete - set status to INACTIVE
        product.status = 'INACTIVE'
        product.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Producto "{product.name}" eliminado exitosamente.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar el producto: {str(e)}'
        })




def crear_dispositivo(request):
    try:
        usuario = Usuario.objects.get(user=request.user)
        user_organization = usuario.organization
        
        # Check if user is in "Encargado EcoEnergy" group
        is_encargado = request.user.groups.filter(name='Encargado EcoEnergy').exists()
        
    except Usuario.DoesNotExist:
        user_organization = None
        is_encargado = False
        messages.error(request, "Please complete your user profile before creating devices.")
        return redirect('some_profile_setup_url')
    
    if request.method == 'POST':
        form = DeviceForm(
            request.POST, 
            request.FILES, 
            user=request.user,
            is_encargado=is_encargado,
            user_organization=user_organization
        )
        if form.is_valid():
            device = form.save()
            messages.success(request, "Dispositivo creado exitosamente.")
            return redirect('lista_dispositivos')
    else:
        form = DeviceForm(
            user=request.user,
            is_encargado=is_encargado,
            user_organization=user_organization
        )
    
    context = {
        'title': 'Crear Dispositivo',
        'form': form,
        'organization': user_organization,
        'is_encargado': is_encargado,
    }
    return render(request, 'dispositivos/crear.html', context)
@login_required
@cliente_admin()
def editar_dispositivo(request, pk):
    # Get organization based on user role
    if request.user.groups.filter(name='Encargado EcoEnergy').exists():
        # Encargado can edit any device
        dispositivo = get_object_or_404(Device, pk=pk)
        organization = dispositivo.organization  # Use the device's organization for form context
    elif hasattr(request.user, 'usuario'):
        # Others can only edit devices from their organization
        organization = request.user.usuario.organization
        dispositivo = get_object_or_404(Device, pk=pk, organization=organization)
    else:
        messages.error(request, "❌ No tienes una organización asignada.")
        return redirect('lista_dispositivos')
    
    if request.method == 'POST':
        form = DeviceForm(request.POST, request.FILES, instance=dispositivo, organization=organization)
        if form.is_valid():
            dispositivo = form.save()
            messages.success(request, f'✅ Dispositivo "{dispositivo.name}" actualizado exitosamente!')
            return redirect('lista_dispositivos')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                field_name = form.fields[field].label if field in form.fields else field
                for error in errors:
                    error_messages.append(f"{field_name}: {error}")
            
            if error_messages:
                full_error_message = "\\n• " + "\\n• ".join(error_messages)
                messages.error(request, f"Errores en el formulario:{full_error_message}")
    else:
        form = DeviceForm(instance=dispositivo, organization=organization)
    
    return render(request, "dispositivos/editar_dispositivo.html", {
        "form": form,
        "dispositivo": dispositivo,
        "title": "Editar Dispositivo",
        "organization": organization,
        "is_encargado": request.user.groups.filter(name='Encargado EcoEnergy').exists(),
    })

@login_required
@cliente_admin()
def crear_zona(request):
    organization = get_user_organization(request)
    
    if not organization:
        messages.error(request, "❌ No tienes una organización asignada.")
        return redirect('lista_zonas')
    
    if request.method == 'POST':
        form = ZoneForm(request.POST, organization=organization)
        if form.is_valid():
            zona = form.save(commit=False)
            zona.organization = organization
            zona.save()
            messages.success(request, f'✅ Zona "{zona.name}" creada exitosamente!')
            return redirect('lista_zonas')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                field_name = form.fields[field].label if field in form.fields else field
                for error in errors:
                    error_messages.append(f"{field_name}: {error}")
            
            if error_messages:
                full_error_message = "\\n• " + "\\n• ".join(error_messages)
                messages.error(request, f"Errores en el formulario:{full_error_message}")
    else:
        form = ZoneForm(organization=organization)
    
    return render(request, "zonas/editar_zona.html", {
        "form": form,
        "title": "Crear Zona",
        "organization": organization
    })

@login_required
@cliente_admin()
def editar_zona(request, pk):
    organization = get_user_organization(request)
    zona = get_object_or_404(Zone, pk=pk, organization=organization)
    
    if request.method == 'POST':
        form = ZoneForm(request.POST, instance=zona, organization=organization)
        if form.is_valid():
            zona = form.save()
            messages.success(request, f'✅ Zona "{zona.name}" actualizada exitosamente!')
            return redirect('lista_zonas')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                field_name = form.fields[field].label if field in form.fields else field
                for error in errors:
                    error_messages.append(f"{field_name}: {error}")
            
            if error_messages:
                full_error_message = "\\n• " + "\\n• ".join(error_messages)
                messages.error(request, f"Errores en el formulario:{full_error_message}")
    else:
        form = ZoneForm(instance=zona, organization=organization)
    
    return render(request, "zonas/editar_zona.html", {
        "form": form,
        "zona": zona,
        "title": "Editar Zona",
        "organization": organization
    })
@login_required
@cliente_admin()
@require_POST
def eliminar_dispositivo(request, pk):
    # Get organization based on user role
    if request.user.groups.filter(name='Encargado EcoEnergy').exists():
        # Encargado can delete any device
        dispositivo = get_object_or_404(Device, pk=pk)
    elif hasattr(request.user, 'usuario'):
        # Others can only delete devices from their organization
        organization = request.user.usuario.organization
        dispositivo = get_object_or_404(Device, pk=pk, organization=organization)
    else:
        return JsonResponse({
            'success': False,
            'message': '❌ No tienes permisos para eliminar dispositivos.'
        })
    
    try:
        dispositivo.status = 'INACTIVE'
        dispositivo.save()
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Dispositivo "{dispositivo.name}" eliminado exitosamente.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'❌ Error al eliminar el dispositivo: {str(e)}'
        })

@login_required
@cliente_admin()
@require_POST
def eliminar_zona(request, pk):
    # Get organization based on user role
    if request.user.groups.filter(name='Encargado EcoEnergy').exists():
        # Encargado can delete any zone
        zona = get_object_or_404(Zone, pk=pk)
    elif hasattr(request.user, 'usuario'):
        # Others can only delete zones from their organization
        organization = request.user.usuario.organization
        zona = get_object_or_404(Zone, pk=pk, organization=organization)
    else:
        return JsonResponse({
            'success': False,
            'message': '❌ No tienes permisos para eliminar zonas.'
        })
    
    try:
        # Check if zone has active devices
        if zona.devices.filter(status='ACTIVE').exists():
            return JsonResponse({
                'success': False,
                'message': f'❌ No se puede eliminar la zona "{zona.name}" porque tiene dispositivos asignados.'
            })
        
        zona.status = 'INACTIVE'
        zona.save()
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Zona "{zona.name}" eliminada exitosamente.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'❌ Error al eliminar la zona: {str(e)}'
        })