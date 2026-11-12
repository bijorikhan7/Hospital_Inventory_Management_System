from rest_framework import serializers

from maintenance.models import AssetIssue, Repair


class AssetIssueSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.CharField(source="reported_by.username", read_only=True)
    asset_code = serializers.CharField(source="asset.asset_code", read_only=True)
    asset_name = serializers.CharField(source="asset.name", read_only=True)

    class Meta:
        model = AssetIssue
        fields = (
            "id",
            "asset",
            "asset_code",
            "asset_name",
            "reported_by",
            "reported_by_name",
            "reported_at",
            "issue_type",
            "title",
            "description",
            "priority",
            "status",
            "warranty_claim",
            "resolved_at",
            "resolved_by",
            "resolution_notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "reported_by",
            "reported_at",
            "status",
            "resolved_at",
            "resolved_by",
            "created_at",
            "updated_at",
        )


class RepairSerializer(serializers.ModelSerializer):
    asset_code = serializers.CharField(source="asset.asset_code", read_only=True)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)

    class Meta:
        model = Repair
        fields = (
            "id",
            "issue",
            "asset",
            "asset_code",
            "vendor",
            "vendor_name",
            "sent_date",
            "received_date",
            "repair_type",
            "estimated_cost",
            "actual_cost",
            "warranty_covered",
            "status",
            "remarks",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "asset", "created_at", "updated_at")
