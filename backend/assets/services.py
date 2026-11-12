from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from accounts.models import Employee
from assets.lifecycle import apply_status, assert_transition, log_history
from assets.models import Asset, AssetAssignment, AssetHistory, AssetReplacement


def _fail(message: str):
    raise ValidationError({"detail": message})


def _active_assignment(asset: Asset) -> AssetAssignment | None:
    return asset.assignments.filter(status=AssetAssignment.Status.ACTIVE).select_related("employee").first()


@transaction.atomic
def assign_asset(asset: Asset, employee: Employee, user, remarks: str = "") -> AssetAssignment:
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    if asset.status in {Asset.Status.DISPOSED, Asset.Status.LOST, Asset.Status.REPLACED}:
        _fail(f"A {asset.status.lower()} asset cannot be assigned.")
    if asset.status == Asset.Status.ASSIGNED or _active_assignment(asset):
        _fail("This asset is already assigned to another employee.")
    if asset.status != Asset.Status.AVAILABLE:
        _fail(f"Only available assets can be assigned. Current status is {asset.status}.")
    if not employee.is_active_employee:                                                                     
        _fail("Inactive employee cannot receive a new asset.")

    assert_transition(asset, Asset.Status.ASSIGNED)      
    assignment = AssetAssignment.objects.create(
        asset=asset,
        employee=employee,
        assigned_by=user,
        remarks=remarks,
        status=AssetAssignment.Status.ACTIVE,
    )
    old_status = asset.status
    asset.status = Asset.Status.ASSIGNED
    asset.current_employee = employee
    asset.save()
    log_history(
        asset,
        AssetHistory.Action.ASSIGNED,
        user,
        description=f"Assigned to {employee.name} ({employee.employee_code})",
        old_value={"status": old_status, "employee": None},
        new_value={"status": asset.status, "employee": employee.employee_code},
    )
    return assignment


@transaction.atomic
def return_asset(asset: Asset, user, remarks: str = "") -> AssetAssignment:
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    assignment = _active_assignment(asset)
    if not assignment:
        _fail("Returning an already returned asset is not allowed. No active assignment exists.")
    assignment.status = AssetAssignment.Status.RETURNED
    assignment.returned_at = timezone.now()
    assignment.returned_by = user
    if remarks:
        assignment.remarks = (assignment.remarks + "\n" + remarks).strip()
    assignment.save()
    old_emp = assignment.employee.employee_code
    asset.status = Asset.Status.AVAILABLE
    asset.current_employee = None
    asset.save()
    log_history(
        asset,
        AssetHistory.Action.RETURNED,
        user,
        description=f"Returned from {assignment.employee.name}",
        old_value={"employee": old_emp, "status": Asset.Status.ASSIGNED},
        new_value={"employee": None, "status": Asset.Status.AVAILABLE},
    )
    return assignment


@transaction.atomic
def transfer_asset(asset: Asset, employee: Employee, user, remarks: str = "") -> AssetAssignment:
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    if not employee.is_active_employee:
        _fail("Inactive employee cannot receive a new asset.")
    assignment = _active_assignment(asset)
    if not assignment:
        _fail("Asset must have an active assignment before it can be transferred.")
    if assignment.employee_id == employee.pk:
        _fail("Asset is already assigned to this employee.")
    old_employee = assignment.employee
    assignment.status = AssetAssignment.Status.TRANSFERRED
    assignment.returned_at = timezone.now()
    assignment.returned_by = user
    assignment.save()
    new_assignment = AssetAssignment.objects.create(
        asset=asset,
        employee=employee,
        assigned_by=user,
        remarks=remarks,
        status=AssetAssignment.Status.ACTIVE,
    )
    asset.current_employee = employee
    asset.status = Asset.Status.ASSIGNED
    asset.save()
    log_history(
        asset,
        AssetHistory.Action.TRANSFERRED,
        user,
        description=f"Transferred from {old_employee.name} to {employee.name}",
        old_value={"employee": old_employee.employee_code},
        new_value={"employee": employee.employee_code},
    )
    return new_assignment


@transaction.atomic
def replace_asset(old_asset: Asset, new_asset: Asset, user, reason: str, replacement_date, remarks: str = "") -> AssetReplacement:
    old_asset = Asset.objects.select_for_update().get(pk=old_asset.pk)
    new_asset = Asset.objects.select_for_update().get(pk=new_asset.pk)
    if old_asset.pk == new_asset.pk:
        _fail("An asset cannot replace itself. Old and new assets must be different.")
    if new_asset.status in {Asset.Status.DISPOSED, Asset.Status.LOST, Asset.Status.REPLACED}:
        _fail("Replacement asset is not eligible.")
    active = _active_assignment(old_asset)
    if active:
        return_asset(old_asset, user, remarks="Returned due to replacement")
        old_asset.refresh_from_db()
    apply_status(old_asset, Asset.Status.REPLACED, user, description="Marked replaced")
    old_asset.current_employee = None
    old_asset.save(update_fields=["current_employee", "updated_at"])
    replacement = AssetReplacement.objects.create(
        old_asset=old_asset,
        new_asset=new_asset,
        replacement_date=replacement_date,
        reason=reason,
        approved_by=user,
        remarks=remarks,
    )
    log_history(
        old_asset,
        AssetHistory.Action.REPLACED,
        user,
        description=f"Replaced by {new_asset.asset_code}",
        old_value={"asset": old_asset.asset_code},
        new_value={"asset": new_asset.asset_code},
    )
    log_history(
        new_asset,
        AssetHistory.Action.UPDATED,
        user,
        description=f"Used as replacement for {old_asset.asset_code}",
    )
    return replacement
