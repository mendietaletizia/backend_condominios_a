from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import CuotaMensual, CuotaUnidad, PagoCuota
from .serializers.finanzas_serializer import (
    CuotaMensualSerializer, CuotaUnidadSerializer, CuotaUnidadUpdateSerializer, PagoCuotaSerializer,
    ResumenCuotasSerializer, MorososSerializer
)
from comunidad.models import Unidad
from comunidad.services import NotificacionService

class CuotaMensualViewSet(viewsets.ModelViewSet):
    """Gestión de cuotas mensuales - CU22"""
    queryset = CuotaMensual.objects.all()
    serializer_class = CuotaMensualSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        cuota_mensual = serializer.save(creado_por=self.request.user)
        
        # Generar cuotas automáticamente para todas las unidades activas
        unidades = Unidad.objects.filter(activa=True)
        
        if unidades.exists():
            # Calcular monto por unidad
            monto_por_unidad = cuota_mensual.monto_total / unidades.count()
            
            # Crear cuotas para cada unidad
            for unidad in unidades:
                CuotaUnidad.objects.create(
                    cuota_mensual=cuota_mensual,
                    unidad=unidad,
                    monto=monto_por_unidad,
                    fecha_limite=cuota_mensual.fecha_limite,
                    estado='pendiente'
                )
            
            # Cambiar estado a activa
            cuota_mensual.estado = 'activa'
            cuota_mensual.save()

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        # Verificar si hay pagos asociados
        cuotas_unidad = instance.cuotas_unidad.all()
        total_pagos = sum(cuota.pagos.count() for cuota in cuotas_unidad)
        
        if total_pagos > 0:
            # Si hay pagos, eliminar primero los pagos, luego las cuotas por unidad
            for cuota_unidad in cuotas_unidad:
                cuota_unidad.pagos.all().delete()
            cuotas_unidad.delete()
        else:
            # Si no hay pagos, eliminar directamente las cuotas por unidad
            cuotas_unidad.delete()
        
        instance.delete()

    @action(detail=True, methods=['post'])
    def generar_cuotas_unidades(self, request, pk=None):
        """Generar cuotas automáticamente para todas las unidades o unidades específicas"""
        cuota_mensual = self.get_object()
        
        if cuota_mensual.estado != 'borrador':
            return Response(
                {'error': 'Solo se pueden generar cuotas para cuotas en estado borrador'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener unidades según la selección
        enviar_a_todos = request.data.get('enviar_a_todos', True)
        unidades_seleccionadas = request.data.get('unidades_seleccionadas', [])
        
        if enviar_a_todos:
            unidades = Unidad.objects.filter(activa=True)
        else:
            if not unidades_seleccionadas:
                return Response(
                    {'error': 'Debe seleccionar al menos una unidad'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            unidades = Unidad.objects.filter(id__in=unidades_seleccionadas, activa=True)
        
        if not unidades.exists():
            return Response(
                {'error': 'No hay unidades activas para generar cuotas'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calcular monto por unidad
        monto_por_unidad = cuota_mensual.monto_total / unidades.count()
        
        cuotas_creadas = 0
        for unidad in unidades:
            # Crear cuota para la unidad
            cuota_unidad, created = CuotaUnidad.objects.get_or_create(
                cuota_mensual=cuota_mensual,
                unidad=unidad,
                defaults={
                    'monto': monto_por_unidad,
                    'fecha_limite': cuota_mensual.fecha_limite,
                    'estado': 'pendiente'
                }
            )
            
            if created:
                cuotas_creadas += 1
        
        # Cambiar estado a activa
        cuota_mensual.estado = 'activa'
        cuota_mensual.save()
        
        return Response({
            'message': f'Se generaron {cuotas_creadas} cuotas para {unidades.count()} unidades',
            'monto_por_unidad': monto_por_unidad,
            'total_unidades': unidades.count()
        })

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """Obtener resumen general de cuotas"""
        cuotas = self.get_queryset()
        
        total_cuotas = cuotas.count()
        cuotas_activas = cuotas.filter(estado='activa').count()
        cuotas_cerradas = cuotas.filter(estado='cerrada').count()
        
        # Calcular montos totales
        monto_total = sum(cuota.monto_total for cuota in cuotas)
        monto_cobrado = 0
        monto_pendiente = 0
        
        for cuota in cuotas:
            for cuota_unidad in cuota.cuotas_unidad.all():
                monto_cobrado += cuota_unidad.monto_pagado
                monto_pendiente += cuota_unidad.calcular_saldo_pendiente()
        
        porcentaje_cobranza = (monto_cobrado / monto_total * 100) if monto_total > 0 else 0
        
        return Response({
            'total_cuotas': total_cuotas,
            'cuotas_activas': cuotas_activas,
            'cuotas_cerradas': cuotas_cerradas,
            'monto_total': monto_total,
            'monto_cobrado': monto_cobrado,
            'monto_pendiente': monto_pendiente,
            'porcentaje_cobranza': round(porcentaje_cobranza, 2)
        })

class CuotaUnidadViewSet(viewsets.ModelViewSet):
    """Gestión de cuotas por unidad - CU22"""
    queryset = CuotaUnidad.objects.all()
    serializer_class = CuotaUnidadSerializer
    permission_classes = [IsAuthenticated]


    def get_serializer_class(self):
        """Usar serializer específico según la acción"""
        if self.action in ['update', 'partial_update']:
            return CuotaUnidadUpdateSerializer
        return CuotaUnidadSerializer


    def perform_destroy(self, instance):
        # Eliminar primero todos los pagos asociados
        instance.pagos.all().delete()
        # Luego eliminar la cuota por unidad
        instance.delete()

    @action(detail=False, methods=['get'])
    def morosos(self, request):
        """Obtener lista de residentes morosos"""
        cuotas_vencidas = self.get_queryset().filter(estado='vencida')
        
        morosos = []
        for cuota in cuotas_vencidas:
            # Obtener residente principal
            residente = cuota.unidad.residentes.filter(rol_en_unidad='propietario').first()
            residente_nombre = "Sin residente"
            if residente:
                residente_nombre = f"{residente.persona.nombre} {residente.persona.apellido}"
            
            morosos.append({
                'cuota_id': cuota.id,
                'unidad': cuota.unidad.numero_casa,
                'residente': residente_nombre,
                'mes_año': cuota.cuota_mensual.mes_año,
                'monto_adeudado': cuota.calcular_saldo_pendiente(),
                'dias_vencido': (timezone.now().date() - cuota.fecha_limite).days,
                'fecha_vencimiento': cuota.fecha_limite
            })
        
        return Response(morosos)

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """Obtener cuotas pendientes de pago"""
        cuotas_pendientes = self.get_queryset().filter(estado='pendiente')
        serializer = self.get_serializer(cuotas_pendientes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def vencidas(self, request):
        """Obtener cuotas vencidas"""
        cuotas_vencidas = self.get_queryset().filter(estado='vencida')
        serializer = self.get_serializer(cuotas_vencidas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def registrar_pago(self, request, pk=None):
        """Registrar un pago para una cuota"""
        cuota_unidad = self.get_object()
        monto_pago = Decimal(request.data.get('monto', 0))
        metodo_pago = request.data.get('metodo_pago', 'efectivo')
        observaciones = request.data.get('observaciones', '')
        numero_referencia = request.data.get('numero_referencia', '')
        
        if monto_pago <= 0:
            return Response(
                {'error': 'El monto del pago debe ser mayor a 0'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que no se exceda el monto pendiente
        saldo_pendiente = cuota_unidad.calcular_saldo_pendiente()
        if monto_pago > saldo_pendiente:
            return Response(
                {'error': f'El monto del pago (${monto_pago}) no puede ser mayor al saldo pendiente (${saldo_pendiente})'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear el pago
        pago = PagoCuota.objects.create(
            cuota_unidad=cuota_unidad,
            monto=monto_pago,
            fecha_pago=timezone.now().date(),
            metodo_pago=metodo_pago,
            observaciones=observaciones,
            numero_referencia=numero_referencia,
            registrado_por=request.user
        )
        
        return Response({
            'message': 'Pago registrado exitosamente',
            'pago_id': pago.id,
            'nuevo_estado': cuota_unidad.estado,
            'saldo_pendiente': cuota_unidad.calcular_saldo_pendiente()
        })

class PagoCuotaViewSet(viewsets.ModelViewSet):
    """Gestión de pagos de cuotas - CU22"""
    queryset = PagoCuota.objects.all()
    serializer_class = PagoCuotaSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(registrado_por=self.request.user)

    @action(detail=False, methods=['get'])
    def por_mes(self, request):
        """Obtener pagos por mes/año"""
        mes_año = request.query_params.get('mes_año')
        if not mes_año:
            return Response(
                {'error': 'Debe proporcionar el parámetro mes_año'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pagos = self.get_queryset().filter(
            cuota_unidad__cuota_mensual__mes_año=mes_año
        )
        serializer = self.get_serializer(pagos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def por_unidad(self, request):
        """Obtener pagos por unidad"""
        unidad_id = request.query_params.get('unidad_id')
        if not unidad_id:
            return Response(
                {'error': 'Debe proporcionar el parámetro unidad_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pagos = self.get_queryset().filter(
            cuota_unidad__unidad_id=unidad_id
        )
        serializer = self.get_serializer(pagos, many=True)
        return Response(serializer.data)