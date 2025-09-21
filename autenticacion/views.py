from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from autenticacion.serializers import LoginSerializer
from rest_framework.authtoken.models import Token
from usuarios.models import Empleado, Residentes

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        token, _ = Token.objects.get_or_create(user=user)

        # Determinar el rol del usuario
        empleado = Empleado.objects.filter(usuario=user).first()
        if empleado:
            rol = empleado.cargo
        else:
            # Verificar si es residente
            residente = Residentes.objects.filter(persona__email=user.email).first()
            rol = "Residente" if residente else "Usuario"

        return Response({
            "token": token.key,
            "username": user.username,
            "email": user.email,
            "rol": rol,
            "user_id": user.id
        })


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Borrar token para cerrar sesión
        if hasattr(request, 'auth') and request.auth:
            request.auth.delete()
        return Response({"detail": "Sesión cerrada"}, status=status.HTTP_200_OK)
