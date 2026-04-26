from django.contrib.auth import get_user_model, authenticate
from django.db import IntegrityError
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from users.serializers import SignupSerializer

User = get_user_model()


# ---------------------------
# SIGNUP VIEW
# ---------------------------
class SignupView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SignupSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        # Validate input
        if not serializer.is_valid():
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid input data",
                        "details": serializer.errors,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = serializer.save()
        except IntegrityError:
            return Response(
                {
                    "error": {
                        "code": "USER_EXISTS",
                        "message": "Username already exists",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create token
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                },
                "token": token.key,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------------------
# LOGIN VIEW
# ---------------------------
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        # Basic validation
        if not username or not password:
            return Response(
                {
                    "error": {
                        "code": "MISSING_FIELDS",
                        "message": "Username and password are required",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Authenticate user (SAFE way)
        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid username or password",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create token
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "username": user.username,
                "role": user.role,
            },
            status=status.HTTP_200_OK,
        )