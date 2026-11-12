from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EmployeeViewSet, LoginView, MeViewSet, RefreshView, UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("employees", EmployeeViewSet, basename="employee")
router.register("me", MeViewSet, basename="me")

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="token_refresh"),
    path("", include(router.urls)),
]
