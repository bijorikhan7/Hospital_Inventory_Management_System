from datetime import date, timedelta

from django.conf import settings
from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminOrITStaff
from assets.models import Asset, AssetHistory, Warranty
from maintenance.models import AssetIssue, Repair
from maintenance.services import employee_can_access_asset


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        assets = Asset.objects.all()
        if user.is_employee_role() and user.employee_id:
            assets = assets.filter(current_employee_id=user.employee_id)
        elif user.is_employee_role():
            assets = assets.none()

        counts = assets.aggregate(
            total=Count("id"),
            available=Count("id", filter=Q(status=Asset.Status.AVAILABLE)),
            assigned=Count("id", filter=Q(status=Asset.Status.ASSIGNED)),
            under_repair=Count("id", filter=Q(status=Asset.Status.UNDER_REPAIR)),
            damaged=Count("id", filter=Q(status=Asset.Status.DAMAGED)),
            lost=Count("id", filter=Q(status=Asset.Status.LOST)),
            disposed=Count("id", filter=Q(status=Asset.Status.DISPOSED)),
            replaced=Count("id", filter=Q(status=Asset.Status.REPLACED)),
        )

        today = date.today()
        soon = today + timedelta(days=getattr(settings, "WARRANTY_EXPIRING_DAYS", 30))
        warranties = Warranty.objects.filter(asset_id__in=assets.values("id"))
        latest_ids = []
        # count based on each asset's latest warranty
        from django.db.models import Max

        latest = warranties.values("asset_id").annotate(end=Max("end_date"))
        active_w = expiring_w = expired_w = 0
        for row in latest:
            end = row["end"]
            if end < today:
                expired_w += 1
            elif end <= soon:
                expiring_w += 1
            else:
                active_w += 1

        issues = AssetIssue.objects.filter(asset_id__in=assets.values("id"))
        open_issues = issues.exclude(status__in=[AssetIssue.Status.RESOLVED, AssetIssue.Status.CLOSED, AssetIssue.Status.CANCELLED]).count()
        under_repair_issues = issues.filter(status=AssetIssue.Status.UNDER_REPAIR).count()

        history_qs = AssetHistory.objects.filter(asset_id__in=assets.values("id")).select_related("asset", "performed_by")[:15]
        if user.is_employee_role():
            history_qs = history_qs.none()

        recent = [
            {
                "id": h.id,
                "asset_code": h.asset.asset_code,
                "action": h.action,
                "description": h.description,
                "performed_by": h.performed_by.username if h.performed_by else None,
                "created_at": h.created_at,
            }
            for h in history_qs
        ]

        return Response(
            {
                "assets": counts,
                "warranties": {
                    "active": active_w,
                    "expiring_soon": expiring_w,
                    "expired": expired_w,
                },
                "open_issues": open_issues,
                "assets_under_repair": counts["under_repair"],
                "issues_under_repair": under_repair_issues,
                "recent_activities": recent,
            }
        )
