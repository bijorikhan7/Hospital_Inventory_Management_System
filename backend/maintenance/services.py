from datetime import date, timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from assets.lifecycle import apply_status, log_history
from assets.models import Asset, AssetHistory, Warranty
from maintenance.models import AssetIssue, Repair


def _fail(message: str):
    raise ValidationError({"detail": message})


def employee_can_access_asset(user, asset: Asset) -> bool:
    if user.is_admin() or user.is_it_staff():
        return True
    if user.is_employee_role() and user.employee_id:
        return asset.current_employee_id == user.employee_id
    return False


@transaction.atomic
def report_issue(asset: Asset, user, data: dict) -> AssetIssue:
    asset = Asset.objects.select_related("current_employee").get(pk=asset.pk)
    if not employee_can_access_asset(user, asset):
        _fail("You can only report issues for assets assigned to you.")
    warranty_claim = bool(data.get("warranty_claim"))
    latest = asset.warranties.order_by("-end_date").first()
    if warranty_claim and (not latest or latest.status == "EXPIRED"):
        _fail("Warranty claim can only be set when a warranty is active or expiring soon.")
    issue = AssetIssue.objects.create(
        asset=asset,
        reported_by=user,
        issue_type=data.get("issue_type") or AssetIssue.IssueType.HARDWARE,
        title=data["title"],
        description=data["description"],
        priority=data.get("priority") or AssetIssue.Priority.MEDIUM,
        warranty_claim=warranty_claim,
        status=AssetIssue.Status.OPEN,
    )
    log_history(
        asset,
        AssetHistory.Action.ISSUE_REPORTED,
        user,
        description=issue.title,
        new_value={"issue_id": issue.id, "priority": issue.priority},
    )
    return issue


def review_issue(issue: AssetIssue, user) -> AssetIssue:
    if issue.status not in {AssetIssue.Status.OPEN}:
        _fail("Only open issues can be marked under review.")
    issue.status = AssetIssue.Status.UNDER_REVIEW
    issue.save(update_fields=["status", "updated_at"])
    log_history(issue.asset, AssetHistory.Action.UPDATED, user, description=f"Issue {issue.id} under review")
    return issue


@transaction.atomic
def start_repair(issue: AssetIssue, user, data: dict) -> Repair:
    if issue.status in {AssetIssue.Status.RESOLVED, AssetIssue.Status.CLOSED, AssetIssue.Status.CANCELLED}:
        _fail("Cannot start repair on a closed issue.")
    asset = Asset.objects.select_for_update().get(pk=issue.asset_id)
    repair = Repair.objects.create(
        issue=issue,
        asset=asset,
        vendor_id=data.get("vendor"),
        sent_date=data.get("sent_date"),
        repair_type=data.get("repair_type") or Repair.RepairType.HARDWARE,
        estimated_cost=data.get("estimated_cost"),
        warranty_covered=bool(data.get("warranty_covered")),
        remarks=data.get("remarks") or "",
        status=Repair.Status.PENDING,
    )
    issue.status = AssetIssue.Status.UNDER_REPAIR
    issue.save(update_fields=["status", "updated_at"])
    if asset.status != Asset.Status.UNDER_REPAIR:
        apply_status(asset, Asset.Status.UNDER_REPAIR, user, description=f"Repair started for issue {issue.id}")
    log_history(asset, AssetHistory.Action.SENT_FOR_REPAIR, user, description=f"Repair {repair.id} created")
    return repair


@transaction.atomic
def update_repair(repair: Repair, user, data: dict) -> Repair:
    new_status = data.get("status", repair.status)
    allowed = {
        Repair.Status.PENDING: {Repair.Status.SENT, Repair.Status.IN_PROGRESS, Repair.Status.CANCELLED},
        Repair.Status.SENT: {Repair.Status.IN_PROGRESS, Repair.Status.COMPLETED, Repair.Status.CANCELLED},
        Repair.Status.IN_PROGRESS: {Repair.Status.COMPLETED, Repair.Status.CANCELLED},
        Repair.Status.COMPLETED: set(),
        Repair.Status.CANCELLED: set(),
    }
    if new_status != repair.status and new_status not in allowed.get(repair.status, set()):
        _fail(f"Invalid repair status transition from {repair.status} to {new_status}.")
    if "vendor" in data:
        repair.vendor_id = data["vendor"]
    for field in ("sent_date", "received_date", "repair_type", "estimated_cost", "actual_cost", "warranty_covered", "remarks"):
        if field in data:
            setattr(repair, field, data[field])
    repair.status = new_status
    repair.save()
    asset = repair.asset
    issue = repair.issue
    if new_status == Repair.Status.COMPLETED:
        issue.status = AssetIssue.Status.RESOLVED
        issue.resolved_at = timezone.now()
        issue.resolved_by = user
        issue.resolution_notes = data.get("resolution_notes") or repair.remarks
        issue.save()
        if asset.current_employee_id:
            apply_status(asset, Asset.Status.ASSIGNED, user, description="Repair completed, returned to assignee")
        else:
            apply_status(asset, Asset.Status.AVAILABLE, user, description="Repair completed, asset available")
        log_history(asset, AssetHistory.Action.REPAIR_COMPLETED, user, description=f"Repair {repair.id} completed")
    if new_status == Repair.Status.CANCELLED and issue.status == AssetIssue.Status.UNDER_REPAIR:
        issue.status = AssetIssue.Status.UNDER_REVIEW
        issue.save(update_fields=["status", "updated_at"])
    return repair


@transaction.atomic
def mark_repair_failed(repair: Repair, user, remarks: str = "") -> Asset:
    asset = Asset.objects.select_for_update().get(pk=repair.asset_id)
    apply_status(asset, Asset.Status.DAMAGED, user, description=remarks or "Repair failed")
    repair.remarks = (repair.remarks + "\n" + remarks).strip()
    repair.save(update_fields=["remarks", "updated_at"])
    return asset


def warranty_status_for_asset(asset: Asset) -> str | None:
    warranty = asset.warranties.order_by("-end_date").first()
    return warranty.status if warranty else None
