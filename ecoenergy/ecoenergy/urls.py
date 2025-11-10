
from django.contrib import admin
from django.urls import path, include
from devices.views import dashboard, lista_productos, editar_producto, eliminar_producto, crear_producto, lista_dispositivos, editar_dispositivo, crear_dispositivo, eliminar_dispositivo
from organizations.views import register,profile, usuario_list, errors, editar_perfil, eliminar_usuario
from django.contrib.auth.views import LoginView
from django.views.generic import RedirectView




urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('accounts/login/', LoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('accounts/', include('organizations.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', register, name='register'),
    path('accounts/profile/', profile, name='profile'),
    path('lista_usuarios/', usuario_list, name='lista_usuarios'),
    path('editar_perfil/<int:user_id>/', editar_perfil, name='editar_perfil'),
    path('accounts/<int:pk>/eliminar/', eliminar_usuario, name='eliminar_usuario'),

    #======PRODUCTOS======#
    path('productos/', lista_productos, name='lista_productos'),
    path('productos/crear/', crear_producto, name='crear_producto'),
    path('productos/<int:pk>/editar/', editar_producto, name='editar_producto'),
    path('productos/<int:pk>/eliminar/', eliminar_producto, name='eliminar_producto'),

    #=====DISPOSITIVOS=====#
    path('dispositivos/', lista_dispositivos, name='lista_dispositivos'),
    path('dispositivos/crear/', crear_dispositivo, name='crear_dispositivo'),
    path('dispositivos/<int:pk>/editar/', editar_dispositivo, name='editar_dispositivo'),
    path('dispositivos/<int:pk>/eliminar/',eliminar_dispositivo, name='eliminar_dispositivo'),
]
handler404 = 'organizations.views.errors'
handler403 = 'organizations.views.errors' 
handler500 = 'organizations.views.errors'
handler400 = 'organizations.views.errors'