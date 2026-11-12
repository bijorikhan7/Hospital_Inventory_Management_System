from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Employee, User
from assets.models import Asset, AssetCategory, Vendor, Warranty


class Command(BaseCommand):
    help = "Load safe development sample data. Never run this as a substitute for production setup."

    def add_arguments(self, parser):
        parser.add_argument("--reset-dev-users", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "role": User.Role.ADMIN, "is_staff": True, "is_superuser": True},
        )
        admin.role = User.Role.ADMIN
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("Admin@12345")
        admin.save()

        it_emp, _ = Employee.objects.get_or_create(
            employee_code="EMP-IT-0001",
            defaults={
                "name": "Nadia Rahman",
                "email": "itstaff@example.com",
                "phone": "01700000001",
                "department": "IT",
                "designation": "IT Officer",
                "join_date": date(2022, 1, 10),
                "location": "Dhaka HQ",
                "status": Employee.Status.ACTIVE,
            },
        )
        staff, _ = User.objects.get_or_create(
            username="itstaff",
            defaults={"email": "itstaff@example.com", "role": User.Role.IT_STAFF, "employee": it_emp},
        )
        staff.role = User.Role.IT_STAFF
        staff.employee = it_emp
        staff.set_password("Staff@12345")
        staff.save()

        emp, _ = Employee.objects.get_or_create(
            employee_code="EMP-0001",
            defaults={
                "name": "Rahim Ahmed",
                "email": "rahim@example.com",
                "phone": "01700000002",
                "department": "Finance",
                "designation": "Accountant",
                "join_date": date(2023, 3, 1),
                "location": "Dhaka HQ",
                "status": Employee.Status.ACTIVE,
            },
        )
        emp_user, _ = User.objects.get_or_create(
            username="employee",
            defaults={"email": "rahim@example.com", "role": User.Role.EMPLOYEE, "employee": emp},
        )
        emp_user.role = User.Role.EMPLOYEE
        emp_user.employee = emp
        emp_user.set_password("Employee@12345")
        emp_user.save()

        Employee.objects.get_or_create(
            employee_code="EMP-0002",
            defaults={
                "name": "Sadia Karim",
                "email": "sadia@example.com",
                "phone": "01700000003",
                "department": "HR",
                "designation": "HR Executive",
                "join_date": date(2021, 8, 15),
                "location": "Chattogram",
                "status": Employee.Status.ACTIVE,
            },
        )
        Employee.objects.get_or_create(
            employee_code="EMP-0003",
            defaults={
                "name": "Inactive User",
                "email": "inactive@example.com",
                "department": "Operations",
                "designation": "Coordinator",
                "status": Employee.Status.INACTIVE,
                "location": "Dhaka HQ",
            },
        )

        categories = [
            ("Laptop", "LAP", "Notebook computers"),
            ("Monitor", "MON", "Displays"),
            ("Desktop", "DESK", "Desktop PCs"),
            ("Printer", "PRN", "Printers"),
            ("UPS", "UPS", "Uninterruptible power supplies"),
            ("Router", "RTR", "Network routers"),
            ("Switch", "SWT", "Network switches"),
            ("Phone", "PHN", "Mobile phones"),
        ]
        cat_map = {}
        for name, code, desc in categories:
            obj, _ = AssetCategory.objects.get_or_create(code=code, defaults={"name": name, "description": desc})
            cat_map[code] = obj

        vendor, _ = Vendor.objects.get_or_create(
            name="TechSource Ltd",
            defaults={
                "contact_person": "Jamal Uddin",
                "phone": "01800000000",
                "email": "sales@techsource.example",
                "address": "Motijheel, Dhaka",
                "vendor_type": Vendor.VendorType.SUPPLIER,
            },
        )
        Vendor.objects.get_or_create(
            name="FixIt Repair Center",
            defaults={"vendor_type": Vendor.VendorType.REPAIR_CENTER, "phone": "01900000000"},
        )

        samples = [
            ("IT-LAP-0001", "LAP", "Dell Latitude 5440", "Dell", "Latitude 5440", "DL5440-ABC123"),
            ("IT-LAP-0002", "LAP", "HP EliteBook 840", "HP", "EliteBook 840", "HP840-XYZ789"),
            ("IT-MON-0001", "MON", "Dell 24 Monitor", "Dell", "P2422H", "MON-111222"),
            ("IT-UPS-0001", "UPS", "APC 1500VA UPS", "APC", "BR1500G", "UPS-998877"),
        ]
        for code, cat, name, brand, model, serial in samples:
            asset, created = Asset.objects.get_or_create(
                asset_code=code,
                defaults={
                    "category": cat_map[cat],
                    "name": name,
                    "brand": brand,
                    "model": model,
                    "serial_number": serial,
                    "location": "Dhaka HQ",
                    "vendor": vendor,
                    "purchase_date": date(2024, 5, 14),
                    "purchase_price": 120000,
                    "status": Asset.Status.AVAILABLE,
                    "condition": Asset.Condition.GOOD,
                },
            )
            if created:
                Warranty.objects.create(
                    asset=asset,
                    provider="Dell" if "Dell" in brand else brand,
                    start_date=date(2024, 5, 14),
                    end_date=date.today() + timedelta(days=400),
                    warranty_number=f"W-{serial}",
                )

        # one expiring warranty
        Asset.objects.filter(asset_code="IT-UPS-0001").update(condition=Asset.Condition.FAIR)
        ups = Asset.objects.get(asset_code="IT-UPS-0001")
        Warranty.objects.filter(asset=ups).update(end_date=date.today() + timedelta(days=10))

        self.stdout.write(self.style.SUCCESS("Development seed complete."))
        self.stdout.write("Users (development only):")
        self.stdout.write("  admin / Admin@12345")
        self.stdout.write("  itstaff / Staff@12345")
        self.stdout.write("  employee / Employee@12345")
