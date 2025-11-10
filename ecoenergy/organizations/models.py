from django.db import models
from django.contrib.auth.models import User, Group
from django.core.validators import RegexValidator, MinLengthValidator
from django.core.exceptions import ValidationError

class Organization(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True, help_text="Whether the organization is active")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

def user_avatar_path(instance, filename):
    return f'avatars/user_{instance.user.id}/{filename}'

class Usuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='users')
    
    name = models.CharField(
        max_length=100,
        validators=[
            MinLengthValidator(2, "Name must be at least 2 characters long."),
            RegexValidator(
                regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                message="Name can only contain letters and spaces.",
                code='invalid_name'
            )
        ],
        help_text="Full name of the user"
    )
    
    phone_regex = RegexValidator(
        regex=r'^\d{9}$',
        message="Phone number must be exactly 10 digits."
    )
    
    phone = models.CharField(
        max_length=9,
        validators=[phone_regex],
        help_text="10-digit phone number"
    )
    
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        help_text="User profile image",
        blank=True,
        null=True,
        default='avatars/default_avatar.png'
    )
    
    def clean(self):
        super().clean()
        if self.phone and len(self.phone) != 9:
            raise ValidationError({'phone': 'Phone number must be exactly 10 digits.'})
        if self.name and len(self.name.strip()) < 2:
            raise ValidationError({'name': 'Name must be at least 2 characters long.'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"