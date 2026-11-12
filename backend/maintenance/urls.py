from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IssueViewSet, RepairViewSet

router = DefaultRouter()
router.register("issues", IssueViewSet, basename="issue")
router.register("repairs", RepairViewSet, basename="repair")

urlpatterns = [path("", include(router.urls))]
