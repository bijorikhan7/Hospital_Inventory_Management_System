from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AssetViewSet,
    CategoryViewSet,
    HistoryViewSet,
    PurchaseViewSet,
    ReplacementViewSet,
    VendorViewSet,
    WarrantyViewSet,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("vendors", VendorViewSet, basename="vendor")
router.register("assets", AssetViewSet, basename="asset")
router.register("purchases", PurchaseViewSet, basename="purchase")
router.register("warranties", WarrantyViewSet, basename="warranty")
router.register("history", HistoryViewSet, basename="history")
router.register("replacements", ReplacementViewSet, basename="replacement")

urlpatterns = [
    path("", include(router.urls)),
]
