from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Employee, User
from .permissions import IsAdminRole
from .serializers import (
    AuthTokenSerializer,
    EmployeeSerializer,
    UserCreateSerializer,
    UserSerializer,
)


class LoginView(TokenObtainPairView):
    serializer_class = AuthTokenSerializer
    permission_classes = []
    authentication_classes = []


class RefreshView(TokenRefreshView):
    permission_classes = []
    authentication_classes = []


class MeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        return Response(UserSerializer(request.user).data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related("employee").all().order_by("id")
    permission_classes = [IsAdminRole]
    search_fields = ("username", "email", "first_name", "last_name")
    filterset_fields = ("role", "is_active")

    def get_serializer_class(self):
        if self.action in {"create"}:
            return UserCreateSerializer
        return UserSerializer

    def perform_update(self, serializer):
        password = self.request.data.get("password")
        user = serializer.save()
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    search_fields = ("employee_code", "name", "email", "department", "designation")
    filterset_fields = ("status", "department", "location")
    ordering_fields = ("employee_code", "name", "department")

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_employee_role() and user.employee_id:
            return qs.filter(pk=user.employee_id)
        return qs
