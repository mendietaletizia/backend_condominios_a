from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status


class AnalyzeImageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        image = request.data.get('image')
        if not image:
            return Response({"error": "Falta el archivo 'image'"}, status=status.HTTP_400_BAD_REQUEST)

        # Implementación placeholder segura: no llama a proveedores externos.
        # Aquí podrías integrar un proveedor IA usando variables de entorno.
        # Devolvemos un resultado de ejemplo para no bloquear el flujo en Railway.
        result = {
            "ok": True,
            "model": "placeholder:v1",
            "summary": "Imagen recibida y analizada localmente (mock)",
            "labels": [
                {"name": "objeto", "confidence": 0.85},
                {"name": "escena", "confidence": 0.62}
            ]
        }
        return Response(result)


