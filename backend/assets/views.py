from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import Employee
from accounts.permissions import IsAdminOrITStaff, IsAdminRole
from assets.filters import AssetFilter
from assets.lifecycle import apply_status, generate_asset_code
from assets.models import (
    Asset,
    AssetAssignment,
    AssetCategory,
    AssetHistory,
    AssetReplacement,
    Purchase,
    Vendor,
    Warranty,
)
from assets.qr import qr_png_response
from assets.serializers import (
    AssetAssignmentSerializer,
    AssetCategorySerializer,
    AssetHistorySerializer,
    AssetListSerializer,
    AssetReplacementSerializer,
    AssetSerializer,
    AssignSerializer,
    PurchaseSerializer,
    ReturnSerializer,
    TransferSerializer,
    VendorSerializer,
    WarrantySerializer,
)
from assets.services import assign_asset, replace_asset, return_asset, transfer_asset


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = AssetCategory.objects.all()
    serializer_class = AssetCategorySerializer
    search_fields = ("name", "code")
    filterset_fields = ("is_active",)

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [IsAuthenticated()]
        return [IsAdminRole()]


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    search_fields = ("name", "contact_person", "email")
    filterset_fields = ("vendor_type", "is_active")

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [IsAdminOrITStaff()]
        return [IsAdminRole()]


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.select_related("category", "vendor", "current_employee").prefetch_related("warranties")
    filterset_class = AssetFilter
    search_fields = (
        "asset_code",
        "name",
        "brand",
        "model",
        "serial_number",
        "current_employee__name",
        "location",
    )
    ordering_fields = ("asset_code", "name", "status", "purchase_date", "created_at")

    def get_serializer_class(self):
        if self.action == "list":
            return AssetListSerializer
        return AssetSerializer

    def get_permissions(self):
        staff_write = {
            "create",
            "update",
            "partial_update",
            "assign",
            "return_asset_action",
            "transfer",
            "status",
            "history",
            "assignments",
        }
        if self.action in staff_write:
            return [IsAdminOrITStaff()]
        if self.action == "destroy":
            return [IsAdminRole()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_employee_role():
            if not user.employee_id:
                return qs.none()
            return qs.filter(current_employee_id=user.employee_id)
        return qs

    def perform_create(self, serializer):
        category = serializer.validated_data["category"]
        code = serializer.validated_data.get("asset_code")
        if not code:
            serializer.validated_data["asset_code"] = generate_asset_code(category)
        serializer.save()

    def perform_destroy(self, instance):
        raise ValidationError("Assets cannot be deleted. Dispose or replace them instead.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.get_serializer(instance).data
        if request.user.is_employee_role():
            data.pop("purchase_price", None)
        return Response(data)

    @action(detail=False, methods=["get"], url_path="by-code/(?P<code>[^/.]+)")
    def by_code(self, request, code=None):
        asset = get_object_or_404(Asset, asset_code=code.upper())
        serializer = AssetSerializer(asset, context={"request": request})
        data = serializer.data
        if request.user.is_employee_role():
            data.pop("purchase_price", None)
        return Response(data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrITStaff])
    def assign(self, request, pk=None):
        asset = self.get_object()
        ser = AssignSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        employee = get_object_or_404(Employee, pk=ser.validated_data["employee_id"])
        assignment = assign_asset(asset, employee, request.user, ser.validated_data.get("remarks", ""))
        return Response(AssetAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrITStaff])
    def return_asset_action(self, request, pk=None):
        asset = self.get_object()
        ser = ReturnSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        assignment = return_asset(asset, request.user, ser.validated_data.get("remarks", ""))
        return Response(AssetAssignmentSerializer(assignment).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrITStaff])
    def transfer(self, request, pk=None):
        asset = self.get_object()
        ser = TransferSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        employee = get_object_or_404(Employee, pk=ser.validated_data["employee_id"])
        assignment = transfer_asset(asset, employee, request.user, ser.validated_data.get("remarks", ""))
        return Response(AssetAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], permission_classes=[IsAdminOrITStaff])
    def history(self, request, pk=None):
        asset = self.get_object()
        qs = asset.history.select_related("performed_by")
        page = self.paginate_queryset(qs)
        ser = AssetHistorySerializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(ser.data)
        return Response(ser.data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def warranty(self, request, pk=None):
        asset = self.get_object()
        ser = WarrantySerializer(asset.warranties.all(), many=True)
        return Response(ser.data)

    @action(detail=True, methods=["get"], url_path="qr")
    def qr(self, request, pk=None):
        asset = self.get_object()
        return qr_png_response(asset.qr_payload(), f"{asset.asset_code}.png")

    @action(detail=True, methods=["get"], permission_classes=[IsAdminOrITStaff])
    def assignments(self, request, pk=None):
        asset = self.get_object()
        ser = AssetAssignmentSerializer(asset.assignments.select_related("employee"), many=True)
        return Response(ser.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrITStaff])
    def status(self, request, pk=None):
        asset = self.get_object()
        new_status = request.data.get("status")
        remarks = request.data.get("remarks", "")
        if not new_status:
            raise ValidationError("status is required.")
        if request.user.is_it_staff() and new_status in {Asset.Status.DISPOSED, Asset.Status.REPLACED}:
            raise PermissionDenied("IT staff cannot dispose or replace assets. Ask an administrator.")

        if new_status in {Asset.Status.LOST, Asset.Status.DISPOSED, Asset.Status.DAMAGED}:
            if asset.assignments.filter(status="ACTIVE").exists():
                return_asset(asset, request.user, remarks=f"Closed for {new_status}")
                asset.refresh_from_db()
        apply_status(asset, new_status, request.user, description=remarks)
        asset.refresh_from_db()
        return Response(AssetSerializer(asset, context={"request": request}).data)


# bind return URL name to return_asset_action
AssetViewSet.return_asset_action.url_path = "return"
AssetViewSet.return_asset_action.url_name = "return"


class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.select_related("asset", "vendor")
    serializer_class = PurchaseSerializer
    search_fields = ("invoice_number", "purchase_order", "asset__asset_code")
    filterset_fields = ("vendor", "asset")

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD"):
            return [IsAdminOrITStaff()]
        return [IsAdminRole()]

    def perform_create(self, serializer):
        purchase = serializer.save()
        from assets.lifecycle import log_history
        from assets.models import AssetHistory

        log_history(
            purchase.asset,
            AssetHistory.Action.PURCHASED,
            self.request.user,
            description=f"Invoice {purchase.invoice_number}",
        )
        if purchase.unit_price and (purchase.asset.purchase_price is None):
            purchase.asset.purchase_price = purchase.unit_price
            purchase.asset.purchase_date = purchase.purchase_date
            purchase.asset.vendor = purchase.vendor
            purchase.asset.save(update_fields=["purchase_price", "purchase_date", "vendor", "updated_at"])


class WarrantyViewSet(viewsets.ModelViewSet):
    queryset = Warranty.objects.select_related("asset")
    serializer_class = WarrantySerializer
    filterset_fields = ("asset", "warranty_type")

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD"):
            return [IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_employee_role() and user.employee_id:
            return qs.filter(asset__current_employee_id=user.employee_id)
        return qs

    def perform_create(self, serializer):
        w = serializer.save()
        from assets.lifecycle import log_history
        from assets.models import AssetHistory

        log_history(w.asset, AssetHistory.Action.WARRANTY_UPDATED, self.request.user, description="Warranty created")

    def perform_update(self, serializer):
        w = serializer.save()
        from assets.lifecycle import log_history
        from assets.models import AssetHistory

        log_history(w.asset, AssetHistory.Action.WARRANTY_UPDATED, self.request.user, description="Warranty updated")


class HistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AssetHistory.objects.select_related("asset", "performed_by")
    serializer_class = AssetHistorySerializer
    permission_classes = [IsAdminOrITStaff]
    filterset_fields = ("asset", "action")
    search_fields = ("description", "asset__asset_code")

    http_method_names = ["get", "head", "options"]


class ReplacementViewSet(viewsets.ModelViewSet):
    queryset = AssetReplacement.objects.select_related("old_asset", "new_asset", "approved_by")
    serializer_class = AssetReplacementSerializer
    permission_classes = [IsAdminOrITStaff]
    http_method_names = ["get", "post", "head", "options"]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        replacement = replace_asset(
            ser.validated_data["old_asset"],
            ser.validated_data["new_asset"],
            request.user,
            ser.validated_data["reason"],
            ser.validated_data["replacement_date"],
            ser.validated_data.get("remarks", ""),
        )
        return Response(AssetReplacementSerializer(replacement).data, status=status.HTTP_201_CREATED)
