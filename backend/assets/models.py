from datetime import date, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from common.models import TimeStampedModel


class AssetCategory(TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)
    code = models.CharField(max_length=16, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Asset categories"

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        self.code = self.code.upper().strip()
        super().save(*args, **kwargs)


class Vendor(TimeStampedModel):
    class VendorType(models.TextChoices):
        SUPPLIER = "SUPPLIER", "Supplier"
        MANUFACTURER = "MANUFACTURER", "Manufacturer"
        REPAIR_CENTER = "REPAIR_CENTER", "Repair Center"
        SERVICE_PROVIDER = "SERVICE_PROVIDER", "Service Provider"
        OTHER = "OTHER", "Other"

    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    vendor_type = models.CharField(max_length=32, choices=VendorType.choices, default=VendorType.SUPPLIER)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["vendor_type", "is_active"])]

    def __str__(self) -> str:
        return self.name


class Asset(TimeStampedModel):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        ASSIGNED = "ASSIGNED", "Assigned"
        UNDER_REPAIR = "UNDER_REPAIR", "Under Repair"
        DAMAGED = "DAMAGED", "Damaged"
        LOST = "LOST", "Lost"
        DISPOSED = "DISPOSED", "Disposed"
        REPLACED = "REPLACED", "Replaced"

    class Condition(models.TextChoices):
        NEW = "NEW", "New"
        GOOD = "GOOD", "Good"
        FAIR = "FAIR", "Fair"
        DAMAGED = "DAMAGED", "Damaged"
        CRITICAL = "CRITICAL", "Critical"

    ASSIGNABLE_STATUSES = {Status.AVAILABLE}
    NON_ASSIGNABLE_STATUSES = {Status.DISPOSED, Status.LOST, Status.REPLACED, Status.ASSIGNED}

    asset_code = models.CharField(max_length=32, unique=True)
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT, related_name="assets")
    name = models.CharField(max_length=150)
    brand = models.CharField(max_length=80, blank=True)
    model = models.CharField(max_length=80, blank=True)
    serial_number = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    vendor = models.ForeignKey(Vendor, null=True, blank=True, on_delete=models.SET_NULL, related_name="assets")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.NEW)
    location = models.CharField(max_length=120, blank=True)
    current_employee = models.ForeignKey(
        "accounts.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_assets",
    )

    class Meta:
        ordering = ["asset_code"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["condition"]),
            models.Index(fields=["location"]),
            models.Index(fields=["brand"]),
            models.Index(fields=["name"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=~Q(serial_number=""),
                name="asset_serial_not_empty",
            )
        ]

    def __str__(self) -> str:
        return f"{self.asset_code} {self.name}"

    def clean(self):
        if self.serial_number:
            self.serial_number = self.serial_number.strip()
        if not self.serial_number:
            raise ValidationError({"serial_number": "Serial number is required."})
        if self.status == self.Status.ASSIGNED and not self.current_employee_id:
            raise ValidationError("Assigned assets must have a current employee.")
        if self.status != self.Status.ASSIGNED and self.current_employee_id:
            raise ValidationError("Only assigned assets may have a current employee.")

    def qr_payload(self) -> str:
        return f"{settings.FRONTEND_URL}/assets/{self.asset_code}"

    @property
    def active_warranty(self):
        return self.warranties.order_by("-end_date").first()


class Purchase(TimeStampedModel):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="purchases")
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="purchases")
    invoice_number = models.CharField(max_length=80)
    purchase_date = models.DateField()
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    invoice_file = models.FileField(upload_to="invoices/", blank=True, null=True)
    purchase_order = models.CharField(max_length=80, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-purchase_date"]

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class Warranty(TimeStampedModel):
    class WarrantyType(models.TextChoices):
        MANUFACTURER = "MANUFACTURER", "Manufacturer"
        EXTENDED = "EXTENDED", "Extended"
        VENDOR = "VENDOR", "Vendor"
        OTHER = "OTHER", "Other"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="warranties")
    provider = models.CharField(max_length=150)
    warranty_type = models.CharField(max_length=32, choices=WarrantyType.choices, default=WarrantyType.MANUFACTURER)
    start_date = models.DateField()
    end_date = models.DateField()
    warranty_number = models.CharField(max_length=80, blank=True)
    terms = models.TextField(blank=True)
    document = models.FileField(upload_to="warranties/", blank=True, null=True)

    class Meta:
        ordering = ["-end_date"]
        indexes = [models.Index(fields=["end_date"])]

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError("Warranty end date must be on or after start date.")

    @property
    def status(self) -> str:
        today = date.today()
        if self.end_date < today:
            return "EXPIRED"
        soon = today + timedelta(days=getattr(settings, "WARRANTY_EXPIRING_DAYS", 30))
        if self.end_date <= soon:
            return "EXPIRING_SOON"
        return "ACTIVE"

    @property
    def is_active(self) -> bool:
        return self.status in {"ACTIVE", "EXPIRING_SOON"}


class AssetAssignment(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        RETURNED = "RETURNED", "Returned"
        TRANSFERRED = "TRANSFERRED", "Transferred"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="assignments")
    employee = models.ForeignKey("accounts.Employee", on_delete=models.PROTECT, related_name="assignments")
    assigned_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assignments_made"
    )
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assignments_returned",
    )
    remarks = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["-assigned_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["asset"],
                condition=Q(status="ACTIVE"),
                name="one_active_assignment_per_asset",
            )
        ]


class AssetReplacement(TimeStampedModel):
    old_asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="replacements_as_old")
    new_asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="replacements_as_new")
    replacement_date = models.DateField()
    reason = models.TextField()
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="approved_replacements"
    )
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-replacement_date"]

    def clean(self):
        if self.old_asset_id == self.new_asset_id:
            raise ValidationError("An asset cannot replace itself.")


class AssetHistory(models.Model):
    class Action(models.TextChoices):
        CREATED = "CREATED", "Created"
        UPDATED = "UPDATED", "Updated"
        PURCHASED = "PURCHASED", "Purchased"
        ASSIGNED = "ASSIGNED", "Assigned"
        RETURNED = "RETURNED", "Returned"
        TRANSFERRED = "TRANSFERRED", "Transferred"
        ISSUE_REPORTED = "ISSUE_REPORTED", "Issue Reported"
        SENT_FOR_REPAIR = "SENT_FOR_REPAIR", "Sent for Repair"
        REPAIR_COMPLETED = "REPAIR_COMPLETED", "Repair Completed"
        DAMAGED = "DAMAGED", "Damaged"
        LOST = "LOST", "Lost"
        REPLACED = "REPLACED", "Replaced"
        DISPOSED = "DISPOSED", "Disposed"
        WARRANTY_UPDATED = "WARRANTY_UPDATED", "Warranty Updated"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="history")
    action = models.CharField(max_length=32, choices=Action.choices)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="asset_history"
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Asset history"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Asset history records cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Asset history records cannot be deleted.")
