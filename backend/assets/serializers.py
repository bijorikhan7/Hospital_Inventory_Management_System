from rest_framework import serializers

from assets.lifecycle import generate_asset_code, log_history
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
from maintenance.services import warranty_status_for_asset


class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetCategory
        fields = ("id", "name", "code", "description", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = (
            "id",
            "name",
            "contact_person",
            "phone",
            "email",
            "address",
            "vendor_type",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class WarrantySerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Warranty
        fields = (
            "id",
            "asset",
            "provider",
            "warranty_type",
            "start_date",
            "end_date",
            "warranty_number",
            "terms",
            "document",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "status", "created_at", "updated_at")


class PurchaseSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Purchase
        fields = (
            "id",
            "asset",
            "vendor",
            "invoice_number",
            "purchase_date",
            "quantity",
            "unit_price",
            "total_price",
            "invoice_file",
            "purchase_order",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "total_price", "created_at", "updated_at")


class AssetListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_code = serializers.CharField(source="category.code", read_only=True)
    employee_name = serializers.CharField(source="current_employee.name", read_only=True)
    warranty_status = serializers.SerializerMethodField()
    warranty_until = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = (
            "id",
            "asset_code",
            "name",
            "brand",
            "model",
            "serial_number",
            "status",
            "condition",
            "location",
            "category",
            "category_name",
            "category_code",
            "current_employee",
            "employee_name",
            "warranty_status",
            "warranty_until",
            "purchase_date",
            "created_at",
        )

    def get_warranty_status(self, obj):
        return warranty_status_for_asset(obj)

    def get_warranty_until(self, obj):
        w = obj.warranties.all()[:1]
        return w[0].end_date if w else None


class AssetSerializer(serializers.ModelSerializer):
    asset_code = serializers.CharField(required=False, allow_blank=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    employee_name = serializers.CharField(source="current_employee.name", read_only=True)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    warranty_status = serializers.SerializerMethodField()
    qr_payload = serializers.SerializerMethodField()
    warranties = WarrantySerializer(many=True, read_only=True)

    class Meta:
        model = Asset
        fields = (
            "id",
            "asset_code",
            "category",
            "category_name",
            "name",
            "brand",
            "model",
            "serial_number",
            "description",
            "purchase_date",
            "purchase_price",
            "vendor",
            "vendor_name",
            "status",
            "condition",
            "location",
            "current_employee",
            "employee_name",
            "warranty_status",
            "qr_payload",
            "warranties",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "status", "current_employee", "created_at", "updated_at")

    def get_warranty_status(self, obj):
        return warranty_status_for_asset(obj)

    def get_qr_payload(self, obj):
        return obj.qr_payload()

    def validate_asset_code(self, value):
        value = (value or "").strip()
        if not value:
            return value
        qs = Asset.objects.filter(asset_code=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Asset code must be unique.")
        return value

    def create(self, validated_data):
        if not validated_data.get("asset_code"):
            validated_data["asset_code"] = generate_asset_code(validated_data["category"])
        asset = super().create(validated_data)
        log_history(asset, "CREATED", self.context["request"].user, description="Asset created")
        return asset

    def update(self, instance, validated_data):
        validated_data.pop("status", None)
        validated_data.pop("current_employee", None)
        user = self.context["request"].user
        if user.is_employee_role():
            raise serializers.ValidationError("Employees cannot modify assets.")
        if user.is_it_staff():
            validated_data.pop("purchase_price", None)
        old = {"name": instance.name, "condition": instance.condition}
        asset = super().update(instance, validated_data)
        log_history(asset, "UPDATED", user, description="Asset updated", old_value=old)
        return asset


class AssetAssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name", read_only=True)
    asset_code = serializers.CharField(source="asset.asset_code", read_only=True)

    class Meta:
        model = AssetAssignment
        fields = (
            "id",
            "asset",
            "asset_code",
            "employee",
            "employee_name",
            "assigned_at",
            "returned_at",
            "assigned_by",
            "returned_by",
            "remarks",
            "status",
        )
        read_only_fields = fields


class AssetHistorySerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(source="performed_by.username", read_only=True)

    class Meta:
        model = AssetHistory
        fields = (
            "id",
            "asset",
            "action",
            "old_value",
            "new_value",
            "performed_by",
            "performed_by_name",
            "description",
            "created_at",
        )
        read_only_fields = fields


class AssetReplacementSerializer(serializers.ModelSerializer):
    old_asset_code = serializers.CharField(source="old_asset.asset_code", read_only=True)
    new_asset_code = serializers.CharField(source="new_asset.asset_code", read_only=True)

    class Meta:
        model = AssetReplacement
        fields = (
            "id",
            "old_asset",
            "new_asset",
            "old_asset_code",
            "new_asset_code",
            "replacement_date",
            "reason",
            "approved_by",
            "remarks",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "approved_by", "created_at", "updated_at")


class AssignSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    remarks = serializers.CharField(required=False, allow_blank=True, default="")


class TransferSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    remarks = serializers.CharField(required=False, allow_blank=True, default="")


class ReturnSerializer(serializers.Serializer):
    remarks = serializers.CharField(required=False, allow_blank=True, default="")
