from django import forms

from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from .models import Product, Category, Device, Zone, Measurement, AlertRule, Organization

class BaseForm(forms.ModelForm):
    """Base form with SweetAlert error collection"""
    
    def get_sweetalert_errors(self):
        """Collect all form errors for SweetAlert display"""
        errors = []
        for field, field_errors in self.errors.items():
            field_label = self.fields[field].label if field in self.fields else field
            for error in field_errors:
                errors.append(f"• {field_label}: {error}")
        return errors

class ProductForm(BaseForm):
    # Custom validators
    sku_validator = RegexValidator(
        regex=r'^[A-Z0-9-]+$',
        message='SKU solo puede contener letras mayúsculas, números y guiones.',
        code='invalid_sku'
    )
    
    # Override the sku field to add validator
    sku = forms.CharField(
        max_length=80,
        validators=[sku_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: DEL-OPT-3090',
            'pattern': '[A-Z0-9-]+',
            'title': 'Solo letras mayúsculas, números y guiones'
        })
    )
    
    nominal_voltage_v = forms.FloatField(
        required=False,
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '220',
            'step': '0.1',
            'min': '0',
            'max': '1000'
        })
    )
    
    max_current_a = forms.FloatField(
        required=False,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '5.0',
            'step': '0.1',
            'min': '0',
            'max': '100'
        })
    )
    
    standby_power_w = forms.FloatField(
        required=False,
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '10.5',
            'step': '0.1',
            'min': '0',
            'max': '1000'
        })
    )

    class Meta:
        model = Product
        fields = [
            'name', 'category', 'sku', 'manufacturer', 'model_name', 
            'description', 'nominal_voltage_v', 'max_current_a', 
            'standby_power_w', 'status'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Dell OptiPlex 3090',
                'minlength': '3',
                'maxlength': '160'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Dell Inc.',
                'maxlength': '120'
            }),
            'model_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: OptiPlex 3090',
                'maxlength': '120'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción detallada del producto...',
                'rows': 4,
                'maxlength': '1000'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'name': 'Nombre del Producto',
            'category': 'Categoría',
            'sku': 'SKU',
            'manufacturer': 'Fabricante',
            'model_name': 'Modelo',
            'description': 'Descripción',
            'nominal_voltage_v': 'Voltaje Nominal (V)',
            'max_current_a': 'Corriente Máxima (A)',
            'standby_power_w': 'Potencia en Standby (W)',
            'status': 'Estado',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")
        return name.strip()

    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if sku:
            # Check for uniqueness (excluding current instance)
            existing = Product.objects.filter(sku=sku)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError("Este SKU ya existe. Debe ser único.")
        return sku

class DeviceForm(BaseForm):
    max_power_w = forms.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50000)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '50000',
            'placeholder': '350'
        })
    )
    
    serial_number = forms.CharField(
        required=False,
        max_length=120,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Opcional',
            'maxlength': '120'
        })
    )

    class Meta:
        model = Device
        fields = [
            'organization', 'name', 'zone', 'product', 'max_power_w', 'image', 
            'serial_number', 'status'
        ]
        widgets = {
            'organization': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: PC-Recepcion',
                'minlength': '3',
                'maxlength': '160'
            }),
            'zone': forms.Select(attrs={'class': 'form-control'}),
            'product': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'organization': 'Organización',
            'name': 'Nombre del Dispositivo',
            'zone': 'Zona',
            'product': 'Producto/Modelo',
            'max_power_w': 'Potencia Máxima (W)',
            'image': 'Imagen',
            'serial_number': 'Número de Serie',
            'status': 'Estado',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.is_encargado = kwargs.pop('is_encargado', False)
        self.user_organization = kwargs.pop('user_organization', None)
        super().__init__(*args, **kwargs)
        
        # Handle organization field based on user role
        if self.is_encargado or (self.user and self.user.is_superuser):
            # Encargados can see all active organizations
            self.fields['organization'].queryset = Organization.objects.filter(is_active=True)
            # Encargados can see all active zones
            self.fields['zone'].queryset = Zone.objects.filter(status='ACTIVE')
        else:
            # Regular users can only see their own organization and its zones
            if self.user_organization:
                self.fields['organization'].queryset = Organization.objects.filter(
                    id=self.user_organization.id, 
                    is_active=True
                )
                self.fields['organization'].initial = self.user_organization
                self.fields['zone'].queryset = Zone.objects.filter(
                    organization=self.user_organization, 
                    status='ACTIVE'
                )
            else:
                self.fields['organization'].queryset = Organization.objects.none()
                self.fields['zone'].queryset = Zone.objects.none()
        
        # Products are available for everyone
        self.fields['product'].queryset = Product.objects.filter(status='ACTIVE')

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")
        
        # Get organization from form data
        organization = self.cleaned_data.get('organization')
        
        # Check uniqueness within organization
        if name and organization:
            existing = Device.objects.filter(
                organization=organization,
                name=name,
                status='ACTIVE'
            )
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError("Ya existe un dispositivo con este nombre en la organización seleccionada.")
        
        return name.strip()

    def clean(self):
        cleaned_data = super().clean()
        
        # Additional validation if needed
        organization = cleaned_data.get('organization')
        zone = cleaned_data.get('zone')
        
        # Ensure zone belongs to selected organization
        if organization and zone:
            if zone.organization != organization:
                raise forms.ValidationError({
                    'zone': 'La zona seleccionada no pertenece a la organización elegida.'
                })
        
        return cleaned_data


class ZoneForm(BaseForm):
    class Meta:
        model = Zone
        fields = ['name', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Oficina Principal',
                'minlength': '3',
                'maxlength': '120'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Nombre de la Zona',
            'status': 'Estado',
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")
        
        # Check uniqueness within organization
        if name and self.organization:
            existing = Zone.objects.filter(
                organization=self.organization,
                name=name,
                status='ACTIVE'
            )
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError("Ya existe una zona con este nombre en tu organización.")
        
        return name.strip()

class MeasurementForm(BaseForm):
    energy_kwh = forms.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(10000)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'min': '0',
            'max': '10000',
            'placeholder': '0.000'
        })
    )

    class Meta:
        model = Measurement
        fields = ['device', 'energy_kwh', 'triggered_alert']
        widgets = {
            'device': forms.Select(attrs={'class': 'form-control'}),
            'triggered_alert': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'device': 'Dispositivo',
            'energy_kwh': 'Energía (kWh)',
            'triggered_alert': 'Alerta Activada',
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        if self.organization:
            self.fields['device'].queryset = Device.objects.filter(
                organization=self.organization, 
                status='ACTIVE'
            )
        
        self.fields['triggered_alert'].queryset = AlertRule.objects.filter(status='ACTIVE')

    def clean_energy_kwh(self):
        energy = self.cleaned_data.get('energy_kwh')
        if energy and energy < 0:
            raise forms.ValidationError("La energía no puede ser negativa.")
        if energy and energy > 10000:
            raise forms.ValidationError("El valor de energía es demasiado alto.")
        return energy

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'sku', 'manufacturer', 'model_name', 
            'description', 'nominal_voltage_v', 'max_current_a', 
            'standby_power_w', 'status'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código SKU único'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Fabricante'
            }),
            'model_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Modelo específico'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del producto',
                'rows': 3
            }),
            'nominal_voltage_v': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '220',
                'step': '0.1'
            }),
            'max_current_a': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '5.0',
                'step': '0.1'
            }),
            'standby_power_w': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '10.5',
                'step': '0.1'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'name': 'Nombre del Producto',
            'category': 'Categoría',
            'sku': 'SKU',
            'manufacturer': 'Fabricante',
            'model_name': 'Modelo',
            'description': 'Descripción',
            'nominal_voltage_v': 'Voltaje Nominal (V)',
            'max_current_a': 'Corriente Máxima (A)',
            'standby_power_w': 'Potencia en Standby (W)',
            'status': 'Estado',
        }
        help_texts = {
            'sku': 'Código único de inventario. No puede repetirse.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active categories in the dropdown
        self.fields['category'].queryset = Category.objects.filter(status='ACTIVE')