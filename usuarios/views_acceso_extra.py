from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from usuarios.models import PlacaVehiculo, PlacaInvitado, Vehiculo, Invitado, Residentes

class AccesoExtraViewSet:
    """Funcionalidades extra para gestión de accesos"""
    
    @action(detail=False, methods=['get'])
    def lista_placas_autorizadas(self, request):
        """Obtener lista unificada de todas las placas autorizadas para gestión de accesos"""
        try:
            placas_autorizadas = []
            
            # 1. Placas de vehículos de residentes
            placas_residentes = PlacaVehiculo.objects.filter(activo=True).select_related('residente__persona')
            for placa in placas_residentes:
                placas_autorizadas.append({
                    'id': f'residente_{placa.id}',
                    'placa': placa.placa,
                    'tipo': 'Residente',
                    'marca': placa.marca,
                    'modelo': placa.modelo,
                    'color': placa.color,
                    'propietario': placa.residente.persona.nombre,
                    'visitante': None,
                    'fecha_vencimiento': None,
                    'fecha_registro': placa.fecha_registro.isoformat() if placa.fecha_registro else None,
                    'estado': 'Activo'
                })
            
            # 2. Placas de vehículos de invitados (solo activos y no vencidos)
            placas_invitados = PlacaInvitado.objects.filter(
                activo=True,
                fecha_vencimiento__gte=timezone.now()
            ).select_related('residente__persona')
            
            for placa in placas_invitados:
                placas_autorizadas.append({
                    'id': f'invitado_{placa.id}',
                    'placa': placa.placa,
                    'tipo': 'Invitado',
                    'marca': placa.marca or 'N/A',
                    'modelo': placa.modelo or 'N/A',
                    'color': placa.color or 'N/A',
                    'propietario': placa.residente.persona.nombre,
                    'visitante': placa.nombre_visitante,
                    'fecha_vencimiento': placa.fecha_vencimiento.isoformat() if placa.fecha_vencimiento else None,
                    'fecha_registro': placa.fecha_registro.isoformat() if placa.fecha_registro else None,
                    'estado': 'Activo'
                })
            
            # 3. Vehículos del sistema original
            vehiculos_originales = Vehiculo.objects.all()
            for vehiculo in vehiculos_originales:
                placas_autorizadas.append({
                    'id': f'original_{vehiculo.placa}',
                    'placa': vehiculo.placa,
                    'tipo': 'Sistema Original',
                    'marca': vehiculo.marca,
                    'modelo': vehiculo.modelo,
                    'color': vehiculo.color,
                    'propietario': 'N/A',
                    'visitante': None,
                    'fecha_vencimiento': None,
                    'fecha_registro': None,
                    'estado': 'Activo'
                })
            
            # 4. Invitados con vehículos del sistema original
            invitados_con_vehiculo = Invitado.objects.filter(
                activo=True,
                vehiculo_placa__isnull=False
            ).exclude(vehiculo_placa='').select_related('residente__persona')
            
            for invitado in invitados_con_vehiculo:
                # Verificar si no está vencido
                if invitado.fecha_fin and invitado.fecha_fin < timezone.now():
                    continue
                    
                placas_autorizadas.append({
                    'id': f'invitado_original_{invitado.id}',
                    'placa': invitado.vehiculo_placa,
                    'tipo': 'Invitado (Original)',
                    'marca': 'N/A',
                    'modelo': 'N/A',
                    'color': 'N/A',
                    'propietario': invitado.residente.persona.nombre if invitado.residente else 'N/A',
                    'visitante': invitado.nombre,
                    'fecha_vencimiento': invitado.fecha_fin.isoformat() if invitado.fecha_fin else None,
                    'fecha_registro': invitado.fecha_inicio.isoformat() if invitado.fecha_inicio else None,
                    'estado': 'Activo'
                })
            
            return Response({
                'placas_autorizadas': placas_autorizadas,
                'total': len(placas_autorizadas),
                'resumen': {
                    'residentes': len([p for p in placas_autorizadas if p['tipo'] == 'Residente']),
                    'invitados': len([p for p in placas_autorizadas if 'Invitado' in p['tipo']]),
                    'sistema_original': len([p for p in placas_autorizadas if p['tipo'] == 'Sistema Original'])
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error al obtener lista de placas autorizadas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

