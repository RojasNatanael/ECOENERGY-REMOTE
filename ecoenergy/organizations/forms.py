from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from .models import Usuario, Organization

from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django import forms
import re

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Required. Enter a valid email address.",
        label="Email"
    )
    
    name = forms.CharField(
        max_length=100,
        validators=[],
        help_text="Full name of the user (letters and spaces only)",
        label="Nombre"
    )
    
    phone = forms.CharField(
        max_length=9,
        help_text="10-digit phone number (numbers only)",
        label="Numero telefonico"
    )
    
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=True,
        empty_label="Select Organization",
        label="Organizacion"
    )
    
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        empty_label="Select Role",
        help_text="Select the user's role/group",
        label="Tipo de usuario"
    )
    
    avatar = forms.ImageField(
        required=False,
        help_text="Optional profile picture",
        label="Avatar"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'name', 'phone', 'organization', 'group', 'avatar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = "Contraseña"
        self.fields['password2'].label = "Confirmar contraseña"
        
        # Change username label
        self.fields['username'].label = "Nombre de usuario"
        # Remove the password help text that shows validation rules
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
        self.fields['name'].help_text = ''
        self.fields['phone'].help_text = ''
        self.fields['email'].help_text = ''
        self.fields['group'].help_text = ''
        self.fields['avatar'].help_text = ''
        self.fields['username'].help_text = ''

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError('El email es requerido.')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este email ya está registrado.')
        
        # Basic email format validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError('Por favor ingresa un email válido.')
        
        return email

    def clean_name(self):
        name = self.cleaned_data.get('name')
        
        if not name:
            raise ValidationError('El nombre es requerido.')
        
        # Check minimum length
        if len(name.strip()) < 2:
            raise ValidationError('El nombre debe tener al menos 2 caracteres.')
        
        # Check maximum length
        if len(name) > 100:
            raise ValidationError('El nombre no puede tener más de 100 caracteres.')
        
        # Check if name contains only letters and spaces
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', name):
            raise ValidationError('El nombre solo puede contener letras y espacios.')
        
        return name.strip()

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        
        if not phone:
            raise ValidationError('El número de teléfono es requerido.')
        
        # Remove any spaces or dashes
        phone = phone.replace(' ', '').replace('-', '')
        
        # Check if phone contains only numbers
        if not phone.isdigit():
            raise ValidationError('El número de teléfono solo puede contener números.')
        
        # Check if phone has exactly 10 digits
        if len(phone) != 9:
            raise ValidationError('El número de teléfono debe tener exactamente 9 dígitos.')
        
        # Check if phone is already registered
        if Usuario.objects.filter(phone=phone).exists():
            raise ValidationError('Este número de teléfono ya está registrado.')
        
        return phone

    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        if not username:
            raise ValidationError('El nombre de usuario es requerido.')
        
        # Check minimum length
        if len(username) < 3:
            raise ValidationError('El nombre de usuario debe tener al menos 3 caracteres.')
        
        # Check for allowed characters
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError('El nombre de usuario solo puede contener letras, números y guiones bajos.')
        
        return username

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        
        if avatar:
            # Check file size (max 5MB)
            if avatar.size > 5 * 1024 * 1024:
                raise ValidationError('La imagen no puede ser mayor a 5MB.')
            
            # Check file extension
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif']
            extension = avatar.name.split('.')[-1].lower()
            if extension not in valid_extensions:
                raise ValidationError('Formato de imagen no válido. Use JPG, PNG o GIF.')
        
        return avatar

    def clean(self):
        cleaned_data = super().clean()
        
        # Cross-field validation example
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Las contraseñas no coinciden.')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']  # Ensure email is saved
       
        if commit:
            user.save()
            
            # Add user to selected group
            group = self.cleaned_data['group']
            user.groups.add(group)
            
            # Create Usuario profile with organization
            Usuario.objects.create(
                user=user,
                name=self.cleaned_data['name'],
                phone=self.cleaned_data['phone'],
                organization=self.cleaned_data['organization'],
                avatar=self.cleaned_data.get('avatar')
            )
        return user




class UserProfileForm(forms.ModelForm):
    # User fields
    email = forms.EmailField(required=True, label="Correo electrónico")
    first_name = forms.CharField(required=False, label="Nombre")
    last_name = forms.CharField(required=False, label="Apellido")
    
    # Usuario fields
    name = forms.CharField(max_length=100, label="Nombre completo")
    phone = forms.CharField(max_length=9, label="Teléfono")
    
    # Password change fields (optional)
    current_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="Contraseña actual"
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="Nueva contraseña"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="Confirmar nueva contraseña"
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Populate initial data from Usuario model
        if self.user and hasattr(self.user, 'usuario'):
            usuario = self.user.usuario
            self.fields['name'].initial = usuario.name
            self.fields['phone'].initial = usuario.phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise ValidationError('Este correo electrónico ya está en uso.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and len(phone) != 9:
            raise ValidationError('El número de teléfono debe tener 9 dígitos.')
        if not phone.isdigit():
            raise ValidationError('El número de teléfono solo puede contener números.')
        

    def clean(self):
        cleaned_data = super().clean()
        
        # Password validation
        current_password = cleaned_data.get('current_password')
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if any([current_password, new_password1, new_password2]):
            # All password fields must be filled
            if not all([current_password, new_password1, new_password2]):
                raise ValidationError('Para cambiar la contraseña, debe completar todos los campos de contraseña.')

            # Verify current password
            if not self.user.check_password(current_password):
                self.add_error('current_password', 'La contraseña actual es incorrecta.')

            # Check if new passwords match
            if new_password1 and new_password2 and new_password1 != new_password2:
                self.add_error('new_password2', 'Las nuevas contraseñas no coinciden.')

            # Check password strength
            if new_password1 and len(new_password1) < 8:
                self.add_error('new_password1', 'La contraseña debe tener al menos 8 caracteres.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Update User fields
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            
            # Update or create Usuario profile
            usuario, created = Usuario.objects.get_or_create(user=user)
            usuario.name = self.cleaned_data['name']
            usuario.phone = self.cleaned_data['phone']
            usuario.save()
            
            # Update password if provided
            new_password = self.cleaned_data.get('new_password1')
            if new_password:
                user.set_password(new_password)
                user.save()
        
        return user




class AdminUserProfileForm(forms.ModelForm):
    # User fields
    email = forms.EmailField(required=True, label="Correo electrónico")
    first_name = forms.CharField(required=False, label="Nombre")
    last_name = forms.CharField(required=False, label="Apellido")
    
    # Usuario fields
    name = forms.CharField(max_length=100, label="Nombre completo")
    phone = forms.CharField(max_length=10, label="Teléfono")
    
    # Admin-only fields
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=True,
        label="Organización"
    )
    
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        label="Rol de usuario"
    )
    
    is_active = forms.BooleanField(
        required=False,
        label="Usuario activo",
        help_text="Desmarque para desactivar este usuario"
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'is_active']

    def __init__(self, *args, **kwargs):
        self.target_user = kwargs.pop('target_user', None)
        super().__init__(*args, **kwargs)
        
        # Populate initial data from Usuario model
        if self.target_user and hasattr(self.target_user, 'usuario'):
            usuario = self.target_user.usuario
            self.fields['name'].initial = usuario.name
            self.fields['phone'].initial = usuario.phone
            self.fields['organization'].initial = usuario.organization
            
            # Get the first group (assuming one group per user)
            if self.target_user.groups.exists():
                self.fields['group'].initial = self.target_user.groups.first()
            
            self.fields['is_active'].initial = self.target_user.is_active

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.target_user.pk).exists():
            raise ValidationError('Este correo electrónico ya está en uso.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and len(phone) != 9:
            raise ValidationError('El número de teléfono debe tener 9 dígitos.')
        
        # Check if phone is already used by another user
        if phone and Usuario.objects.filter(phone=phone).exclude(user=self.target_user).exists():
            raise ValidationError('Este número de teléfono ya está en uso.')
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Update User fields
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = self.cleaned_data['is_active']
        
        if commit:
            user.save()
            
            # Update user groups
            user.groups.clear()
            user.groups.add(self.cleaned_data['group'])
            
            # Update or create Usuario profile
            usuario, created = Usuario.objects.get_or_create(user=user)
            usuario.name = self.cleaned_data['name']
            usuario.phone = self.cleaned_data['phone']
            usuario.organization = self.cleaned_data['organization']
            usuario.save()
        
        return user

