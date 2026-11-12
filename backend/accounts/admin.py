from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Employee, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "is_active", "employee")
    list_filter = ("role", "is_active")
    fieldsets = DjangoUserAdmin.fieldsets + (("Role", {"fields": ("role", "employee")}),)
    add_fieldsets = DjangoUserAdmin.add_fieldsets + ((None, {"fields": ("email", "role", "employee")}),)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_code", "name", "department", "status")
    search_fields = ("employee_code", "name", "email")
