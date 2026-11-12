from django.contrib.auth.models import AbstractUser
from django.db import models

from common.models import TimeStampedModel


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        IT_STAFF = "IT_STAFF", "IT Staff"
        EMPLOYEE = "EMPLOYEE", "Employee"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    employee = models.OneToOneField(
        "Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="user_account",
    )

    REQUIRED_FIELDS = ["email"]

    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN and self.is_active

    def is_it_staff(self) -> bool:
        return self.role == self.Role.IT_STAFF and self.is_active

    def is_employee_role(self) -> bool:
        return self.role == self.Role.EMPLOYEE and self.is_active


class Employee(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    employee_code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=32, blank=True)
    department = models.CharField(max_length=120)
    designation = models.CharField(max_length=120)
    join_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["employee_code"]
        indexes = [
            models.Index(fields=["department"]),
            models.Index(fields=["status"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return f"{self.employee_code} — {self.name}"

    @property
    def is_active_employee(self) -> bool:
        return self.status == self.Status.ACTIVE
