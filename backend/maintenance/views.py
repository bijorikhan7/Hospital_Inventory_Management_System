from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdminOrITStaff
from assets.models import Asset
from maintenance.models import AssetIssue, Repair
from maintenance.serializers import AssetIssueSerializer, RepairSerializer
from maintenance.services import employee_can_access_asset, report_issue, review_issue, start_repair, update_repair


class IssueViewSet(viewsets.ModelViewSet):
    queryset = AssetIssue.objects.select_related("asset", "reported_by")
    serializer_class = AssetIssueSerializer
    filterset_fields = ("status", "priority", "asset", "warranty_claim")
    search_fields = ("title", "description", "asset__asset_code")
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_employee_role() and user.employee_id:
            return qs.filter(asset__current_employee_id=user.employee_id)
        if user.is_admin() or user.is_it_staff():
            return qs
        return qs.none()

    def create(self, request, *args, **kwargs):
        asset_id = request.data.get("asset")
        asset = get_object_or_404(Asset, pk=asset_id)
        issue = report_issue(asset, request.user, request.data)
        return Response(AssetIssueSerializer(issue).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        if not (request.user.is_admin() or request.user.is_it_staff()):
            return Response({"success": False, "message": "Not permitted."}, status=403)
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrITStaff])
    def review(self, request, pk=None):
        issue = review_issue(self.get_object(), request.user)
        return Response(AssetIssueSerializer(issue).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrITStaff])
    def start_repair(self, request, pk=None):
        repair = start_repair(self.get_object(), request.user, request.data)
        return Response(RepairSerializer(repair).data, status=status.HTTP_201_CREATED)


class RepairViewSet(viewsets.ModelViewSet):
    queryset = Repair.objects.select_related("asset", "issue", "vendor")
    serializer_class = RepairSerializer
    permission_classes = [IsAdminOrITStaff]
    filterset_fields = ("status", "asset", "vendor", "warranty_covered")
    http_method_names = ["get", "patch", "post", "head", "options"]

    def create(self, request, *args, **kwargs):
        issue = get_object_or_404(AssetIssue, pk=request.data.get("issue"))
        repair = start_repair(issue, request.user, request.data)
        return Response(RepairSerializer(repair).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        repair = update_repair(self.get_object(), request.user, request.data)
        return Response(RepairSerializer(repair).data)
