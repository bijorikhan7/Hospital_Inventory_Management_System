from datetime import date, timedelta
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Employee, User
from assets.models import Asset, AssetCategory, AssetHistory, Vendor, Warranty
from assets.services import assign_asset, return_asset, transfer_asset, replace_asset
from maintenance.models import AssetIssue, Repair
from maintenance.services import report_issue, start_repair, update_repair


class BaseAPITest(APITestCase):
    def setUp(self):
        self.category = AssetCategory.objects.create(name="Laptop", code="LAP")
        self.vendor = Vendor.objects.create(name="Vendor Co", vendor_type=Vendor.VendorType.SUPPLIER)
        self.emp_active = Employee.objects.create(
            employee_code="EMP-1",
            name="Rahim Ahmed",
            email="rahim@example.com",
            department="Finance",
            designation="Accountant",
            status=Employee.Status.ACTIVE,
        )
        self.emp_other = Employee.objects.create(
            employee_code="EMP-2",
            name="Sadia Karim",
            email="sadia@example.com",
            department="HR",
            designation="HR",
            status=Employee.Status.ACTIVE,
        )
        self.emp_inactive = Employee.objects.create(
            employee_code="EMP-3",
            name="Inactive",
            email="inactive@example.com",
            department="Ops",
            designation="Coord",
            status=Employee.Status.INACTIVE,
        )
        self.admin = User.objects.create_user(
            username="admin", email="admin@example.com", password="pass12345", role=User.Role.ADMIN
        )
        self.staff = User.objects.create_user(
            username="itstaff",
            email="staff@example.com",
            password="pass12345",
            role=User.Role.IT_STAFF,
            employee=self.emp_other,
        )
        self.employee_user = User.objects.create_user(
            username="employee",
            email="rahim@example.com",
            password="pass12345",
            role=User.Role.EMPLOYEE,
            employee=self.emp_active,
        )
        self.asset = Asset.objects.create(
            asset_code="IT-LAP-0001",
            category=self.category,
            name="Dell Latitude 5440",
            brand="Dell",
            model="5440",
            serial_number="SN-001",
            vendor=self.vendor,
            purchase_price=Decimal("1000.00"),
            status=Asset.Status.AVAILABLE,
        )

    def auth(self, user):
        self.client.force_authenticate(user)

    def login(self, username, password="pass12345"):
        url = "/api/auth/login/"
        return self.client.post(url, {"username": username, "password": password}, format="json")


class AuthenticationTests(BaseAPITest):
    def test_login_returns_jwt_and_role(self):
        res = self.login("admin")
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.data)
        self.assertEqual(res.data["user"]["role"], User.Role.ADMIN)

    def test_invalid_login(self):
        res = self.login("admin", "wrong")
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.data.get("success", True))


class PermissionTests(BaseAPITest):
    def test_employee_cannot_create_user(self):
        self.auth(self.employee_user)
        res = self.client.post(
            "/api/auth/users/",
            {"username": "x", "email": "x@example.com", "password": "Secret12345", "role": "ADMIN"},
            format="json",
        )
        self.assertEqual(res.status_code, 403)

    def test_admin_can_create_user(self):
        self.auth(self.admin)
        res = self.client.post(
            "/api/auth/users/",
            {"username": "newadmin", "email": "n@example.com", "password": "Secret12345", "role": "IT_STAFF"},
            format="json",
        )
        self.assertEqual(res.status_code, 201)

    def test_employee_cannot_see_other_assets(self):
        other = Asset.objects.create(
            asset_code="IT-LAP-0099",
            category=self.category,
            name="Other",
            serial_number="SN-099",
            status=Asset.Status.AVAILABLE,
        )
        self.auth(self.employee_user)
        res = self.client.get(f"/api/assets/{other.id}/")
        self.assertEqual(res.status_code, 404)

    def test_employee_cannot_assign(self):
        self.auth(self.employee_user)
        res = self.client.post(f"/api/assets/{self.asset.id}/assign/", {"employee_id": self.emp_active.id}, format="json")
        self.assertEqual(res.status_code, 403)

    def test_staff_cannot_manage_users(self):
        self.auth(self.staff)
        res = self.client.get("/api/auth/users/")
        self.assertEqual(res.status_code, 403)


class AssetCRUDTests(BaseAPITest):
    def test_create_asset_generates_code(self):
        self.auth(self.admin)
        res = self.client.post(
            "/api/assets/",
            {
                "category": self.category.id,
                "name": "ThinkPad",
                "brand": "Lenovo",
                "model": "T14",
                "serial_number": "SN-NEW-1",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.data["asset_code"].startswith("IT-LAP-"))

    def test_unique_asset_code(self):
        self.auth(self.admin)
        res = self.client.post(
            "/api/assets/",
            {
                "asset_code": "IT-LAP-0001",
                "category": self.category.id,
                "name": "Dup",
                "serial_number": "SN-DUP",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_search_and_filter(self):
        self.auth(self.staff)
        res = self.client.get("/api/assets/?search=Latitude&status=AVAILABLE")
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.data["count"], 1)


class LifecycleTests(BaseAPITest):
    def test_assign_return_transfer(self):
        assign_asset(self.asset, self.emp_active, self.admin)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.ASSIGNED)
        self.assertEqual(self.asset.current_employee, self.emp_active)
        transfer_asset(self.asset, self.emp_other, self.admin)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.current_employee, self.emp_other)
        return_asset(self.asset, self.admin)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.AVAILABLE)
        self.assertIsNone(self.asset.current_employee)

    def test_inactive_employee_rejected(self):
        with self.assertRaises(Exception):
            assign_asset(self.asset, self.emp_inactive, self.admin)

    def test_duplicate_active_assignment(self):
        assign_asset(self.asset, self.emp_active, self.admin)
        with self.assertRaises(Exception):
            assign_asset(self.asset, self.emp_other, self.admin)

    def test_return_already_returned_fails(self):
        assign_asset(self.asset, self.emp_active, self.admin)
        return_asset(self.asset, self.admin)
        with self.assertRaises(Exception):
            return_asset(self.asset, self.admin)

    def test_disposed_cannot_assign(self):
        self.asset.status = Asset.Status.DISPOSED
        self.asset.save()
        with self.assertRaises(Exception):
            assign_asset(self.asset, self.emp_active, self.admin)

    def test_lost_cannot_assign(self):
        self.asset.status = Asset.Status.LOST
        self.asset.save()
        with self.assertRaises(Exception):
            assign_asset(self.asset, self.emp_active, self.admin)

    def test_invalid_status_transition(self):
        from assets.lifecycle import apply_status

        self.asset.status = Asset.Status.DISPOSED
        self.asset.save()
        with self.assertRaises(Exception):
            apply_status(self.asset, Asset.Status.AVAILABLE, self.admin)

    def test_history_recorded(self):
        assign_asset(self.asset, self.emp_active, self.admin)
        self.assertTrue(AssetHistory.objects.filter(asset=self.asset, action=AssetHistory.Action.ASSIGNED).exists())

    def test_history_not_deletable(self):
        assign_asset(self.asset, self.emp_active, self.admin)
        h = AssetHistory.objects.first()
        with self.assertRaises(Exception):
            h.delete()


class WarrantyTests(BaseAPITest):
    def test_warranty_status_calculation(self):
        w = Warranty.objects.create(
            asset=self.asset,
            provider="Dell",
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() + timedelta(days=10),
        )
        self.assertEqual(w.status, "EXPIRING_SOON")
        w.end_date = date.today() + timedelta(days=90)
        w.save()
        w.refresh_from_db()
        self.assertEqual(w.status, "ACTIVE")
        w.end_date = date.today() - timedelta(days=1)
        w.save()
        self.assertEqual(w.status, "EXPIRED")


class IssueRepairTests(BaseAPITest):
    def test_employee_report_own_asset(self):
        assign_asset(self.asset, self.emp_active, self.admin)
        issue = report_issue(
            self.asset,
            self.employee_user,
            {"title": "Broken hinge", "description": "Crack", "priority": "HIGH"},
        )
        self.assertEqual(issue.status, AssetIssue.Status.OPEN)

    def test_employee_cannot_report_others_asset(self):
        with self.assertRaises(Exception):
            report_issue(self.asset, self.employee_user, {"title": "x", "description": "y"})

    def test_repair_workflow(self):
        assign_asset(self.asset, self.emp_active, self.admin)
        issue = report_issue(self.asset, self.employee_user, {"title": "Fan", "description": "Noise"})
        repair = start_repair(issue, self.staff, {"repair_type": Repair.RepairType.HARDWARE})
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.UNDER_REPAIR)
        update_repair(repair, self.staff, {"status": Repair.Status.IN_PROGRESS})
        update_repair(repair, self.staff, {"status": Repair.Status.COMPLETED, "actual_cost": "50.00"})
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.ASSIGNED)

    def test_invalid_repair_transition(self):
        assign_asset(self.asset, self.emp_active, self.admin)
        issue = report_issue(self.asset, self.employee_user, {"title": "x", "description": "y"})
        repair = start_repair(issue, self.staff, {})
        with self.assertRaises(Exception):
            update_repair(repair, self.staff, {"status": Repair.Status.COMPLETED})


class ReplacementTests(BaseAPITest):
    def test_replacement(self):
        new_asset = Asset.objects.create(
            asset_code="IT-LAP-0002",
            category=self.category,
            name="New laptop",
            serial_number="SN-002",
            status=Asset.Status.AVAILABLE,
        )
        assign_asset(self.asset, self.emp_active, self.admin)
        replace_asset(self.asset, new_asset, self.admin, "Motherboard dead", date.today())
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.REPLACED)
        with self.assertRaises(Exception):
            assign_asset(self.asset, self.emp_other, self.admin)

    def test_cannot_replace_self(self):
        with self.assertRaises(Exception):
            replace_asset(self.asset, self.asset, self.admin, "nope", date.today())


class QRAndDashboardTests(BaseAPITest):
    def test_qr_lookup(self):
        self.auth(self.staff)
        res = self.client.get("/api/assets/by-code/IT-LAP-0001/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["asset_code"], "IT-LAP-0001")

    def test_dashboard_stats(self):
        self.auth(self.admin)
        res = self.client.get("/api/dashboard/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["assets"]["total"], 1)
        self.assertEqual(res.data["assets"]["available"], 1)

    def test_employee_hides_purchase_price_on_detail(self):
        assign_asset(self.asset, self.emp_active, self.admin)
        self.auth(self.employee_user)
        res = self.client.get(f"/api/assets/{self.asset.id}/")
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("purchase_price", res.data)
