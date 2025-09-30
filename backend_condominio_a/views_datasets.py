from pathlib import Path
import csv
import json
from typing import Any

from django.http import JsonResponse, Http404
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


class DatasetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, name: str):
        base_dir: Path = settings.BASE_DIR / 'datasets'
        json_path = base_dir / f"{name}.json"
        csv_path = base_dir / f"{name}.csv"

        if json_path.exists():
            try:
                with json_path.open('r', encoding='utf-8') as f:
                    data: Any = json.load(f)
                return JsonResponse({"name": name, "format": "json", "data": data}, safe=False)
            except Exception as exc:  # noqa: BLE001
                return JsonResponse({"error": f"Error leyendo JSON: {exc}"}, status=500)

        if csv_path.exists():
            try:
                with csv_path.open('r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                return JsonResponse({"name": name, "format": "csv", "data": rows}, safe=False)
            except Exception as exc:  # noqa: BLE001
                return JsonResponse({"error": f"Error leyendo CSV: {exc}"}, status=500)

        raise Http404("Dataset no encontrado")


