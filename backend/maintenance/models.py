from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class AssetIssue(TimeStampedModel):
    class IssueType(models.TextChoices):
        HARDWARE = "HARDWARE", "Hardware"
        SOFTWARE = "SOFTWARE", "Software"
        NETWORK = "NETWORK", "Network"
        PHYSICAL_DAMAGE = "PHYSICAL_DAMAGE", "Physical Damage"
        PERFORMANCE = "PERFORMANCE", "Performance"
        OTHER = "OTHER", "Other"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        UNDER_REPAIR = "UNDER_REPAIR", "Under Repair"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"
        CANCELLED = "CANCELLED", "Cancelled"

    asset = models.ForeignKey("assets.Asset", on_delete=models.CASCADE, related_name="issues")
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reported_issues"
    )
    reported_at = models.DateTimeField(auto_now_add=True)
    issue_type = models.CharField(max_length=32, choices=IssueType.choices, default=IssueType.HARDWARE)
    title = models.CharField(max_length=180)
    description = models.TextField()
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    warranty_claim = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resolved_issues",
    )
    resolution_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-reported_at"]
        indexes = [
            models.Index(fields=["status", "priority"]),
        ]


class Repair(TimeStampedModel):
    class RepairType(models.TextChoices):
        HARDWARE = "HARDWARE", "Hardware"
        SOFTWARE = "SOFTWARE", "Software"
        REPLACEMENT_PART = "REPLACEMENT_PART", "Replacement Part"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SENT = "SENT", "Sent"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    issue = models.ForeignKey(AssetIssue, on_delete=models.CASCADE, related_name="repairs")
    asset = models.ForeignKey("assets.Asset", on_delete=models.CASCADE, related_name="repairs")
    vendor = models.ForeignKey(
        "assets.Vendor", null=True, blank=True, on_delete=models.SET_NULL, related_name="repairs"
    )
    sent_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)
    repair_type = models.CharField(max_length=32, choices=RepairType.choices, default=RepairType.HARDWARE)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    warranty_covered = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
