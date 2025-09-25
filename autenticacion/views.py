from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from autenticacion.serializers import LoginSerializer, PlacaInvitadoSerializer
from rest_framework.authtoken.models import Token
from usuarios.models import Empleado, Residentes, PlacaInvitado
from django.utils import timezone

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        token, _ = Token.objects.get_or_create(user=user)

        # Determinar el rol del usuario usando el campo rol del modelo Usuario
        residente_id = None
        if hasattr(user, 'rol') and user.rol:
            rol = user.rol.nombre
        else:
            # Lógica de respaldo: empleado o residente
            empleado = Empleado.objects.filter(usuario=user).first()
            if empleado:
                rol = empleado.cargo
            else:
                residente = Residentes.objects.filter(persona__email=user.email).first()
                if residente:
                    rol = "Residente"
                    residente_id = residente.id
                else:
                    rol = "Usuario"

        return Response({
            "token": token.key,
            "username": user.username,
            "email": user.email,
            "rol": rol,
            "user_id": user.id,
            "residente_id": residente_id
        })


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Borrar token para cerrar sesión
        if hasattr(request, 'auth') and request.auth:
            request.auth.delete()
        return Response({"detail": "Sesión cerrada"}, status=status.HTTP_200_OK)

class PlacaInvitadoListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        placas = PlacaInvitado.objects.all()

        # Filtrar por residente_id si se proporciona
        residente_id = request.query_params.get('residente_id', None)
        if residente_id:
            placas = placas.filter(residente_id=residente_id)

        serializer = PlacaInvitadoSerializer(placas, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PlacaInvitadoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PlacaInvitadoDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return PlacaInvitado.objects.get(pk=pk)
        except PlacaInvitado.DoesNotExist:
            return None

    def get(self, request, pk):
        placa = self.get_object(pk)
        if placa is None:
            return Response({'error': 'Placa no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PlacaInvitadoSerializer(placa)
        return Response(serializer.data)

    def put(self, request, pk):
        placa = self.get_object(pk)
        if placa is None:
            return Response({'error': 'Placa no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PlacaInvitadoSerializer(placa, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        placa = self.get_object(pk)
        if placa is None:
            return Response({'error': 'Placa no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        placa.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class PlacaInvitadoActivasView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        placas_activas = PlacaInvitado.objects.filter(
            activo=True,
            fecha_vencimiento__gte=timezone.now()
        )
        serializer = PlacaInvitadoSerializer(placas_activas, many=True)
        return Response(serializer.data)
