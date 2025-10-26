# apps/devices/models.py
#
# ──────────────────────────────────────────────────────────────────────────────
# Propósito del módulo
# ──────────────────────────────────────────────────────────────────────────────
# Este módulo define el modelo de datos (ORM de Django) para el dominio
# "dispositivos" de EcoEnergy. Incluye:
# - Datos maestros globales (administrados por EcoEnergy): Category, Product, AlertRule
# - Datos por organización/cliente (tenant): Zone, Device, Measurement (+ AlertEvent opcional)
#
# Puntos didácticos incluidos en comentarios:
# - BaseModel con trazabilidad y borrado lógico
# - Meta.db_table / Meta.ordering (cómo cambian nombre de tabla y orden por defecto)
# - Indexes (índices para acelerar búsquedas)
# - TextChoices (enumeraciones legibles)
# - ManyToManyField (relación N:M con "related_name" y "blank")
# - unique_together (unicidad compuesta por columnas)
# - on_delete (qué pasa al borrar registros relacionados)
# - ImageField (carga de imágenes)
# - SET_NULL/PROTECT/CASCADE explicado
#
# Después de crear/editar estos modelos:
# python manage.py makemigrations
# python manage.py migrate
#
# ──────────────────────────────────────────────────────────────────────────────

from django.db import models
from organizations.models import Organization
from django.db.models import Q, F



# ──────────────────────────────────────────────────────────────────────────────
# BaseModel (clase abstracta)
# ──────────────────────────────────────────────────────────────────────────────
class BaseModel(models.Model):
    """
    Clase base con campos comunes:
      - status: estado lógico del registro (Active/InActive)
      - created_at / updated_at: trazabilidad temporal
      - deleted_at: borrado lógico (no elimina físicamente el registro)

    Nota:
      - "abstract = True" en Meta: NO crea una tabla propia; sus campos
        se heredan en las subclases.
    """
    STATUS_CHOICES = [
        ("ACTIVE", "Activo"),
        ("INACTIVE", "Inactivo"),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,        # limita los valores permitidos en el admin y forms
        default="ACTIVE",
        help_text="Estado lógico del registro."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,             # se asigna solo al crear
        help_text="Fecha/hora de creación (solo se setea una vez)."
    )
    updated_at = models.DateTimeField(
        auto_now=True,                 # se actualiza en cada save()
        help_text="Fecha/hora de última actualización."
    )
    deleted_at = models.DateTimeField(
        null=True, blank=True,         # permite null/blank para borrado lógico
        help_text="Marca de borrado lógico; no elimina físicamente el registro."
    )

    class Meta:
        abstract = True                # importante: evita tabla de BaseModel


# ──────────────────────────────────────────────────────────────────────────────
# Datos maestros (globales, administrados por EcoEnergy)
# ──────────────────────────────────────────────────────────────────────────────
class Category(BaseModel):
    """
    Categoría de productos (ej.: HVAC, Lighting, Computers).
    - "unique=True" en name para no duplicar categorías.
    """
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        # db_table: cambia el nombre de la tabla en la BD (por defecto sería "devices_category"
        # si la app se llama "devices"). Aquí lo forzamos a "category".
        db_table = "category"

        # ordering: orden por defecto en consultas como Category.objects.all().
        # Si no se indica, Django no impone un orden.
        ordering = ["name"]

        # verbose_name, verbose_name_plural: nombres legibles en el admin (opcional)
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(BaseModel):
    """
    Catálogo de productos. Un Product puede ser "plantilla" para muchos Device.
    """
    name = models.CharField(max_length=160)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,              # PROTECT: evita borrar Category si hay Products asociados
        related_name="products",               # "category.products.all()" devuelve todos los productos de esta categoría
        help_text="Categoría del producto."
    )
    sku = models.CharField(
        max_length=80,
        unique=True,                           # evita SKU repetidos
        help_text="Código único de inventario (SKU)."
    )
    manufacturer = models.CharField(max_length=120, blank=True)
    model_name = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)

    # Especificaciones opcionales útiles para reportes o validaciones
    nominal_voltage_v = models.FloatField(null=True, blank=True)
    max_current_a = models.FloatField(null=True, blank=True)
    standby_power_w = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "product"

        # indexes: crea índices en BD para acelerar búsquedas/filtrados en estas columnas
        # Ej.: Product.objects.filter(name__icontains="fan") o sku exacto
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["sku"]),
        ]

        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return f"{self.name} ({self.sku})"



class AlertRule(BaseModel):
    """
    Regla de alerta (nombre + severidad + unidad).
    Puede tener umbrales por defecto, pero pueden ser sobrescritos por producto.
    """
    class Severity(models.TextChoices):
        CRITICAL = "CRITICAL", "Critical"
        HIGH     = "HIGH",     "High"
        MEDIUM   = "MEDIUM",   "Medium"
        LOW      = "LOW",      "Low"

    name = models.CharField(max_length=140)
    severity = models.CharField(
        max_length=10,
        choices=Severity.choices,
        default=Severity.MEDIUM,
        help_text="Nivel de severidad de la alerta."
    )
    unit = models.CharField(
        max_length=32,
        default="kWh",
        help_text="Unidad por defecto (kWh, W, A, etc.)."
    )

    # Umbrales por defecto (opcionales). Sirven como fallback si el producto no define override.
    default_min_threshold = models.FloatField(null=True, blank=True, help_text="Umbral mínimo por defecto.")
    default_max_threshold = models.FloatField(null=True, blank=True, help_text="Umbral máximo por defecto.")

    # Relación N:M *con datos extra* en la tabla intermedia ProductAlertRule.
    # OJO: cuando usamos through=, Django NO crea la tabla automática; usamos la nuestra.
    products = models.ManyToManyField(
        "Product",
        through="ProductAlertRule",      # ← Aquí está la “join table” explícita
        related_name="alert_rules",
        blank=True,
        help_text="Productos a los que aplica esta regla (relación N:M con umbrales por producto)."
    )

    class Meta:
        db_table = "alert_rule"
        indexes = [
            models.Index(fields=["severity"]),
            models.Index(fields=["name"]),
        ]
        constraints = [
            # Si ambos defaults existen, exigimos min <= max (en caso contrario el check pasa)
            models.CheckConstraint(
                check=Q(default_min_threshold__isnull=True) |
                      Q(default_max_threshold__isnull=True) |
                      Q(default_min_threshold__lte=F('default_max_threshold')),
                name="alert_rule_default_min_lte_max",
            )
        ]
        unique_together = [("name", "severity")]  # simple para enseñar
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} [{self.severity}]"

    # Helper: obtener el par (min, max) efectivo para un producto dado
    def effective_thresholds_for(self, product):
        """
        Retorna (min, max) usando override de ProductAlertRule si existe;
        si no, usa los defaults de la regla.
        """
        par = getattr(self, "_par_cache", None)
        if par and par.get("product_id") == product.id and par.get("alert_rule_id") == self.id:
            return par["min"], par["max"]

        link = ProductAlertRule.objects.filter(product=product, alert_rule=self).first()
        if link and link.min_threshold is not None and link.max_threshold is not None:
            # Cache sencillo para ahorrar un query si lo llaman varias veces
            self._par_cache = {
                "product_id": product.id,
                "alert_rule_id": self.id,
                "min": link.min_threshold,
                "max": link.max_threshold,
            }
            return link.min_threshold, link.max_threshold
        return self.default_min_threshold, self.default_max_threshold


class ProductAlertRule(BaseModel):
    """
    Tabla intermedia (join table) para la relación N:M entre Product y AlertRule,
    que además guarda datos adicionales: umbrales específicos por producto.

    Esto es exactamente tu idea de 'alerta_producto'.
    """
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,        # Si se borra el producto, caen sus enlaces
        related_name="product_alert_links",
        help_text="Producto al que se aplica la alerta con umbrales específicos."
    )
    alert_rule = models.ForeignKey(
        AlertRule,
        on_delete=models.CASCADE,        # Si se borra la regla, caen sus enlaces
        related_name="product_alert_links",
        help_text="Regla de alerta aplicada a este producto."
    )
    # Overrides por producto (si no quieres override, deja null y usará los defaults de AlertRule)
    min_threshold = models.FloatField(null=True, blank=True, help_text="Umbral mínimo (override).")
    max_threshold = models.FloatField(null=True, blank=True, help_text="Umbral máximo (override).")
    # Si te sirve, también puedes permitir override de unidad:
    unit_override = models.CharField(max_length=32, null=True, blank=True, help_text="Unidad específica (opcional).")

    class Meta:
        db_table = "product_alert_rule"
        # Un producto no debería tener la misma regla repetida:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "alert_rule"],
                name="uix_product_alert_unique"
            ),
            # Si ambos overrides existen, exigimos min <= max
            models.CheckConstraint(
                check=Q(min_threshold__isnull=True) |
                      Q(max_threshold__isnull=True) |
                      Q(min_threshold__lte=F('max_threshold')),
                name="par_min_lte_max",
            ),
        ]
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["alert_rule"]),
            models.Index(fields=["product", "alert_rule"]),  # útil para búsquedas directas
        ]
        ordering = ["product_id", "alert_rule_id"]

    def __str__(self):
        return f"{self.product.name} ⟷ {self.alert_rule.name}"
# ──────────────────────────────────────────────────────────────────────────────
# Datos por organización (tenant): Zone, Device, Measurement, AlertEvent
# ──────────────────────────────────────────────────────────────────────────────
class Zone(BaseModel):
    """
    Zona física dentro de una Organization (cliente).
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,       # PROTECT: para no dejar zonas "huérfanas"
        related_name="zones",
        help_text="Organización (cliente) propietaria de la zona."
    )
    name = models.CharField(max_length=120)

    class Meta:
        db_table = "zone"

        # unique_together: asegura que dentro de una misma organización
        # no se repita el nombre de la zona (pero sí puede repetirse en otra org).
        unique_together = [("organization", "name")]

        # ordering múltiple: 1º por organización (id), 2º por nombre de zona
        ordering = ["organization_id", "name"]

        verbose_name = "Zone"
        verbose_name_plural = "Zones"

    def __str__(self):
        return f"{self.name} @ {self.organization.name}"


class Device(BaseModel):
    """
    Dispositivo instalado en una Organization, ubicado en una Zone
    y basado en un Product del catálogo.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,       # PROTECT: no borrar org si hay devices
        related_name="devices",
        help_text="Organización (cliente) dueña del dispositivo."
    )
    zone = models.ForeignKey(
        Zone,
        on_delete=models.PROTECT,       # PROTECT: no borrar zone si hay devices
        related_name="devices",
        help_text="Zona donde está instalado el dispositivo."
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,       # PROTECT: el device depende del product (catálogo)
        related_name="devices",
        help_text="Producto del que deriva este dispositivo concreto."
    )

    name = models.CharField(max_length=160, help_text="Nombre legible único dentro de la organización.")
    max_power_w = models.PositiveIntegerField(help_text="Potencia máxima (W) para validaciones/reportes.")
    image = models.ImageField(
        upload_to="devices/",           # ruta base en el almacenamiento configurado (MEDIA_ROOT)
        null=True, blank=True,
        help_text="Imagen opcional del dispositivo."
    )
    serial_number = models.CharField(max_length=120, blank=True, help_text="N° de serie (opcional).")

    class Meta:
        db_table = "device"

        # Índices prácticos para listar/filtrar por org, zona o producto
        indexes = [
            models.Index(fields=["organization", "name"]),
            models.Index(fields=["zone"]),
            models.Index(fields=["product"]),
        ]

        # Unicidad compuesta: evita repetir "name" de dispositivo dentro de la misma org.
        unique_together = [("organization", "name")]

        verbose_name = "Device"
        verbose_name_plural = "Devices"

    def __str__(self):
        return f"{self.name} @ {self.organization.name}"


class Measurement(BaseModel):
    """
    Serie temporal de mediciones de un Device.
    - Un Device tiene muchas Measurement (1:N).
    - Opcionalmente, una Measurement puede quedar asociada a una AlertRule
      que fue gatillada por sus valores.
    """
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,       # CASCADE: si se borra el device, se borran sus mediciones
        related_name="measurements",
        help_text="Dispositivo al que pertenece la medición."
    )
    measured_at = models.DateTimeField(
        auto_now_add=True,              # fecha/hora cuando se creó el registro
        help_text="Momento en que se registró la medición."
    )
    # Si capturas energía acumulada, kWh tiene sentido. Si capturas potencia instantánea, usar power_w.
    energy_kwh = models.FloatField(help_text="Energía medida (kWh).")

    triggered_alert = models.ForeignKey(
        AlertRule,
        on_delete=models.SET_NULL,      # SET_NULL: si borran la regla, la medición queda sin alerta
        null=True, blank=True,
        related_name="triggered_measurements",
        help_text="Regla de alerta que coincidió con esta medición (si aplica)."
    )

    class Meta:
        db_table = "measurement"
        indexes = [
            # Índice compuesto: útil para series temporales por dispositivo
            models.Index(fields=["device", "measured_at"]),
            models.Index(fields=["triggered_alert"]),
        ]
        ordering = ["-measured_at"]     # más reciente primero (opcional, para listados)

        verbose_name = "Measurement"
        verbose_name_plural = "Measurements"

    def __str__(self):
        return f"{self.device} - {self.energy_kwh} kWh @ {self.measured_at:%Y-%m-%d %H:%M}"


class AlertEvent(BaseModel):
    """
    (Opcional) Bitácora de eventos de alerta emitidos.
    Útil si quieres una tabla separada de Measurement con el historial de alertas.
    """
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,       # si el device se borra, sus eventos se borran
        related_name="alert_events",
        help_text="Dispositivo donde ocurrió la alerta."
    )
    alert_rule = models.ForeignKey(
        AlertRule,
        on_delete=models.PROTECT,       # no permitimos borrar reglas con eventos históricos
        related_name="alert_events",
        help_text="Regla de alerta que se disparó."
    )
    occurred_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Momento en que se generó el evento de alerta."
    )
    message = models.CharField(
        max_length=240,
        blank=True,
        help_text="Mensaje adicional (opcional)."
    )

    class Meta:
        db_table = "alert_event"
        indexes = [
            models.Index(fields=["device", "occurred_at"]),
            models.Index(fields=["alert_rule"]),
        ]
        ordering = ["-occurred_at"]

        verbose_name = "Alert Event"
        verbose_name_plural = "Alert Events"

    def __str__(self):
        return f"[{self.alert_rule.severity}] {self.alert_rule.name} @ {self.device}"
