from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from autenticacion.serializers import LoginSerializer
from rest_framework.authtoken.models import Token
from usuarios.models import Empleado

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        token, _ = Token.objects.get_or_create(user=user)

        empleado = Empleado.objects.filter(usuario=user).first()
        rol = empleado.cargo if empleado else "Residente"

        return Response({
            "token": token.key,
            "username": user.username,
            "rol": rol
        })


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Borrar token para cerrar sesión
        request.auth.delete()
        return Response({"detail": "Sesión cerrada"}, status=status.HTTP_200_OK)
