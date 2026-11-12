from django.db.models import OuterRef, Subquery
from django_filters import rest_framework as filters

from assets.models import Asset, Warranty


class AssetFilter(filters.FilterSet):
    category = filters.NumberFilter(field_name="category_id")
    status = filters.CharFilter(field_name="status")
    condition = filters.CharFilter(field_name="condition")
    employee = filters.NumberFilter(field_name="current_employee_id")
    department = filters.CharFilter(field_name="current_employee__department")
    location = filters.CharFilter(field_name="location", lookup_expr="icontains")
    purchase_from = filters.DateFilter(field_name="purchase_date", lookup_expr="gte")
    purchase_to = filters.DateFilter(field_name="purchase_date", lookup_expr="lte")
    warranty = filters.CharFilter(method="filter_warranty")

    class Meta:
        model = Asset
        fields = ["category", "status", "condition", "employee", "department"]

    def filter_warranty(self, queryset, name, value):
        latest_end = Warranty.objects.filter(asset_id=OuterRef("pk")).order_by("-end_date").values("end_date")[:1]
        qs = queryset.annotate(_warranty_end=Subquery(latest_end))
        today = __import__("datetime").date.today()
        soon = today + __import__("datetime").timedelta(days=30)
        value = (value or "").upper()
        if value == "ACTIVE":
            return qs.filter(_warranty_end__gt=soon)
        if value == "EXPIRING_SOON":
            return qs.filter(_warranty_end__gte=today, _warranty_end__lte=soon)
        if value == "EXPIRED":
            return qs.filter(_warranty_end__lt=today)
        if value == "NONE":
            return qs.filter(_warranty_end__isnull=True)
        return queryset
