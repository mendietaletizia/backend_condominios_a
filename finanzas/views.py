from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import logging

from .models import CuotaMensual, CuotaUnidad, PagoCuota, Ingreso, ResumenIngresos
from .serializers.finanzas_serializer import (
    CuotaMensualSerializer, CuotaUnidadSerializer, CuotaUnidadUpdateSerializer, PagoCuotaSerializer,
    ResumenCuotasSerializer, MorososSerializer, IngresoSerializer, ResumenIngresosSerializer
)
from comunidad.models import Unidad
from comunidad.services import NotificacionService

logger = logging.getLogger(__name__)

class CuotaMensualViewSet(viewsets.ModelViewSet):
    """Gestión de cuotas mensuales - CU22"""
    queryset = CuotaMensual.objects.all()
    serializer_class = CuotaMensualSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        cuota_mensual = serializer.save(creado_por=self.request.user)
        
        # Obtener unidades según la selección
        enviar_a_todos = self.request.data.get('enviar_a_todos', True)
        unidades_seleccionadas = self.request.data.get('unidades_seleccionadas', [])
        
        if enviar_a_todos:
            unidades = Unidad.objects.filter(activa=True)
        else:
            unidades = Unidad.objects.filter(id__in=unidades_seleccionadas, activa=True)
        
        cuotas_creadas = []
        if unidades.exists():
            # Calcular monto por unidad
            monto_por_unidad = cuota_mensual.monto_total / unidades.count()
            
            # Crear cuotas para cada unidad
            for unidad in unidades:
                cuota_unidad = CuotaUnidad.objects.create(
                    cuota_mensual=cuota_mensual,
                    unidad=unidad,
                    monto=monto_por_unidad,
                    fecha_limite=cuota_mensual.fecha_limite,
                    estado='pendiente'
                )
                cuotas_creadas.append(cuota_unidad)
            
            # Cambiar estado a activa
            cuota_mensual.estado = 'activa'
            cuota_mensual.save()
            
            # Crear notificación automática
            try:
                from comunidad.services import NotificacionService
                notificacion = NotificacionService.crear_notificacion_cuota(cuota_mensual, cuotas_creadas)
                if notificacion:
                    print(f"Notificación de cuota creada: {notificacion.id}")
            except Exception as e:
                print(f"Error creando notificación de cuota: {e}")
        
        # Agregar información de respuesta
        self._cuotas_generadas = len(cuotas_creadas)

    def perform_update(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if hasattr(self, '_cuotas_generadas'):
            response.data['cuotas_generadas'] = self._cuotas_generadas
        return response

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

    @action(detail=True, methods=['delete'])
    def eliminar_cuota_mensual(self, request, pk=None):
        """Eliminar una cuota mensual completa con todas sus cuotas por unidad"""
        cuota_mensual = self.get_object()
        
        # Verificar si hay cuotas pagadas
        cuotas_pagadas = cuota_mensual.cuotas_unidad.filter(estado='pagada').count()
        if cuotas_pagadas > 0:
            return Response(
                {'error': f'No se puede eliminar la cuota mensual porque {cuotas_pagadas} cuota(s) ya han sido pagadas'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si hay cuotas en proceso de pago
        cuotas_procesando = cuota_mensual.cuotas_unidad.filter(estado='procesando').count()
        if cuotas_procesando > 0:
            return Response(
                {'error': f'No se puede eliminar la cuota mensual porque {cuotas_procesando} cuota(s) están siendo procesadas para pago'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si hay pagos parciales
        cuotas_con_pagos = cuota_mensual.cuotas_unidad.filter(monto_pagado__gt=0).count()
        if cuotas_con_pagos > 0:
            return Response(
                {'error': f'No se puede eliminar la cuota mensual porque {cuotas_con_pagos} cuota(s) tienen pagos parciales'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener información antes de eliminar
        cuotas_info = []
        for cuota_unidad in cuota_mensual.cuotas_unidad.all():
            cuotas_info.append({
                'id': cuota_unidad.id,
                'unidad': cuota_unidad.unidad.numero_casa,
                'monto': float(cuota_unidad.monto),
                'estado': cuota_unidad.estado
            })
        
        cuota_mensual_info = {
            'id': cuota_mensual.id,
            'mes_año': cuota_mensual.mes_año,
            'monto_total': float(cuota_mensual.monto_total),
            'estado': cuota_mensual.estado,
            'cuotas_eliminadas': len(cuotas_info)
        }
        
        # Eliminar todas las cuotas por unidad primero
        cuota_mensual.cuotas_unidad.all().delete()
        
        # Eliminar la cuota mensual
        cuota_mensual.delete()
        
        logger.info(f"Cuota mensual eliminada: {cuota_mensual_info} por usuario {request.user.username}")
        
        return Response({
            'message': f'Cuota mensual eliminada exitosamente junto con {len(cuotas_info)} cuotas individuales',
            'cuota_mensual_eliminada': cuota_mensual_info,
            'cuotas_individuales_eliminadas': cuotas_info
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

    @action(detail=True, methods=['post'])
    def iniciar_pago_online(self, request, pk=None):
        """Iniciar proceso de pago online para una cuota"""
        cuota_unidad = self.get_object()
        
        # Verificar que la cuota esté pendiente
        if cuota_unidad.estado not in ['pendiente', 'vencida']:
            return Response(
                {'error': 'Solo se pueden pagar cuotas pendientes o vencidas'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generar ID único para el pago
        payment_id = str(uuid.uuid4())
        
        # Actualizar estado de la cuota
        cuota_unidad.estado = 'procesando'
        cuota_unidad.payment_id = payment_id
        cuota_unidad.payment_status = 'pending'
        cuota_unidad.save()
        
        # Obtener información del residente si está disponible
        try:
            from usuarios.models import Residentes
            residente = Residentes.objects.get(unidad=cuota_unidad.unidad)
            customer_name = f"{residente.persona.nombre} {residente.persona.apellido}"
            customer_email = residente.persona.email or 'residente@condominio.com'
        except:
            customer_name = f'Unidad {cuota_unidad.unidad.numero_casa}'
            customer_email = 'residente@condominio.com'
        
        # Preparar datos para la pasarela
        payment_data = {
            'payment_id': payment_id,
            'amount': float(cuota_unidad.monto),
            'currency': 'BOB',
            'description': f'Cuota {cuota_unidad.cuota_mensual.mes_año} - Unidad {cuota_unidad.unidad.numero_casa}',
            'customer_info': {
                'name': customer_name,
                'email': customer_email,
            },
            'callback_url': f'/api/finanzas/cuotas-unidad/{cuota_unidad.id}/confirmar-pago/',
            'return_url': f'/finanzas/cuotas/{cuota_unidad.id}/pago-exitoso/',
            'cancel_url': f'/finanzas/cuotas/{cuota_unidad.id}/pago-cancelado/'
        }
        
        # Integrar con la pasarela de pago real
        from .services import pasarela_service
        payment_response = pasarela_service.crear_pago(payment_data)
        
        if payment_response['success']:
            cuota_unidad.payment_url = payment_response['payment_url']
            cuota_unidad.save()
            payment_url = payment_response['payment_url']
        else:
            # Si falla la integración, revertir estado
            cuota_unidad.estado = 'pendiente'
            cuota_unidad.payment_id = None
            cuota_unidad.save()
            
            logger.error(f"Error creando pago en pasarela: {payment_response.get('error')}")
            return Response({
                'error': 'Error iniciando pago online',
                'details': payment_response.get('details', 'Error de conexión con la pasarela')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f"Pago iniciado para cuota {cuota_unidad.id}, payment_id: {payment_id}")
        
        return Response({
            'message': 'Pago iniciado exitosamente',
            'payment_id': payment_id,
            'payment_url': payment_url,
            'amount': float(cuota_unidad.monto),
            'status': 'pending'
        })

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def confirmar_pago(self, request, pk=None):
        """Webhook para confirmar pago desde la pasarela"""
        cuota_unidad = self.get_object()
        
        # Obtener datos del webhook
        payment_id = request.data.get('payment_id')
        payment_status = request.data.get('status')  # completed, failed, cancelled
        payment_method = request.data.get('payment_method')
        payment_reference = request.data.get('reference')
        amount_paid = request.data.get('amount')
        signature = request.headers.get('X-Signature', '')
        
        # Validar firma del webhook si está configurada
        from .services import pasarela_service
        if pasarela_service.webhook_secret:
            import json
            payload = json.dumps(request.data, sort_keys=True)
            if not pasarela_service.validar_webhook(payload, signature):
                logger.error(f"Webhook signature validation failed for payment {payment_id}")
                return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Verificar que el payment_id coincida
        if cuota_unidad.payment_id != payment_id:
            logger.error(f"Payment ID mismatch: expected {cuota_unidad.payment_id}, got {payment_id}")
            return Response({'error': 'Payment ID mismatch'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que el monto coincida (opcional pero recomendado)
        if amount_paid and abs(float(amount_paid) - float(cuota_unidad.monto)) > 0.01:
            logger.error(f"Amount mismatch: expected {cuota_unidad.monto}, got {amount_paid}")
            return Response({'error': 'Amount mismatch'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar estado según respuesta de la pasarela
        cuota_unidad.payment_status = payment_status
        cuota_unidad.payment_method = payment_method
        cuota_unidad.payment_reference = payment_reference
        
        if payment_status == 'completed':
            # Pago exitoso
            cuota_unidad.estado = 'pagada'
            cuota_unidad.monto_pagado = cuota_unidad.monto
            cuota_unidad.fecha_pago = timezone.now().date()
            
            # Crear registro de pago
            PagoCuota.objects.create(
                cuota_unidad=cuota_unidad,
                monto=cuota_unidad.monto,
                fecha_pago=timezone.now().date(),
                metodo_pago=payment_method or 'online',
                numero_referencia=payment_reference or payment_id,
                observaciones=f'Pago online confirmado - {payment_id}',
                registrado_por=None  # Sistema automático
            )
            
            # Enviar notificación de pago exitoso
            try:
                from .services import NotificacionPagoService
                NotificacionPagoService.crear_notificacion_pago_exitoso(cuota_unidad)
            except Exception as e:
                logger.error(f"Error enviando notificación de pago: {e}")
                
        elif payment_status == 'failed':
            cuota_unidad.estado = 'fallido'
            # Enviar notificación de pago fallido
            try:
                from .services import NotificacionPagoService
                NotificacionPagoService.crear_notificacion_pago_fallido(cuota_unidad, "El pago fue rechazado por la pasarela")
            except Exception as e:
                logger.error(f"Error enviando notificación de pago fallido: {e}")
                
        elif payment_status == 'cancelled':
            cuota_unidad.estado = 'pendiente'
            cuota_unidad.payment_id = None
            cuota_unidad.payment_url = None
        
        cuota_unidad.save()
        
        logger.info(f"Pago {payment_status} para cuota {cuota_unidad.id}, payment_id: {payment_id}")
        
        return Response({
            'message': f'Pago {payment_status}',
            'cuota_id': cuota_unidad.id,
            'estado': cuota_unidad.estado,
            'payment_id': payment_id
        })

    @action(detail=True, methods=['get'])
    def estado_pago(self, request, pk=None):
        """Obtener estado actual del pago"""
        cuota_unidad = self.get_object()
        
        return Response({
            'cuota_id': cuota_unidad.id,
            'estado': cuota_unidad.estado,
            'payment_id': cuota_unidad.payment_id,
            'payment_status': cuota_unidad.payment_status,
            'payment_url': cuota_unidad.payment_url,
            'monto': float(cuota_unidad.monto),
            'monto_pagado': float(cuota_unidad.monto_pagado),
            'saldo_pendiente': float(cuota_unidad.calcular_saldo_pendiente())
        })

    @action(detail=True, methods=['delete'])
    def eliminar_cuota(self, request, pk=None):
        """Eliminar una cuota por unidad con validaciones"""
        cuota_unidad = self.get_object()
        
        # Validaciones antes de eliminar
        if cuota_unidad.estado == 'pagada':
            return Response(
                {'error': 'No se puede eliminar una cuota que ya ha sido pagada'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if cuota_unidad.estado == 'procesando':
            return Response(
                {'error': 'No se puede eliminar una cuota que está siendo procesada para pago'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if cuota_unidad.monto_pagado > 0:
            return Response(
                {'error': 'No se puede eliminar una cuota que tiene pagos parciales registrados'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si hay pagos asociados
        pagos_count = cuota_unidad.pagos.count()
        if pagos_count > 0:
            return Response(
                {'error': f'No se puede eliminar la cuota porque tiene {pagos_count} pago(s) registrado(s)'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener información antes de eliminar para el log
        cuota_info = {
            'id': cuota_unidad.id,
            'unidad': cuota_unidad.unidad.numero_casa,
            'mes_año': cuota_unidad.cuota_mensual.mes_año,
            'monto': float(cuota_unidad.monto),
            'estado': cuota_unidad.estado
        }
        
        # Eliminar la cuota
        cuota_unidad.delete()
        
        logger.info(f"Cuota eliminada: {cuota_info} por usuario {request.user.username}")
        
        return Response({
            'message': 'Cuota eliminada exitosamente',
            'cuota_eliminada': cuota_info
        })

class PagoCuotaViewSet(viewsets.ModelViewSet):
    """Gestión de pagos de cuotas - CU22"""
    queryset = PagoCuota.objects.all()
    serializer_class = PagoCuotaSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(registrado_por=self.request.user)


class CuotasResidenteViewSet(viewsets.ReadOnlyModelViewSet):
    """Vista para residentes - ver sus cuotas pendientes"""
    serializer_class = CuotaUnidadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filtrar cuotas por unidad del residente autenticado"""
        user = self.request.user
        
        # Obtener la unidad del residente
        try:
            from usuarios.models import Residentes
            residente = Residentes.objects.get(usuario=user)
            unidad = residente.unidad
            return CuotaUnidad.objects.filter(unidad=unidad).order_by('-fecha_creacion')
        except:
            return CuotaUnidad.objects.none()

    @action(detail=False, methods=['get'])
    def mis_cuotas_pendientes(self, request):
        """Obtener cuotas pendientes del residente"""
        cuotas_pendientes = self.get_queryset().filter(estado__in=['pendiente', 'vencida', 'procesando'])
        serializer = self.get_serializer(cuotas_pendientes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def mis_cuotas_pagadas(self, request):
        """Obtener cuotas pagadas del residente"""
        cuotas_pagadas = self.get_queryset().filter(estado='pagada')
        serializer = self.get_serializer(cuotas_pagadas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def pagar_online(self, request, pk=None):
        """Iniciar pago online para una cuota del residente"""
        cuota_unidad = self.get_object()
        
        # Verificar que la cuota pertenece al residente
        user = request.user
        try:
            from usuarios.models import Residentes
            residente = Residentes.objects.get(usuario=user)
            if cuota_unidad.unidad != residente.unidad:
                return Response(
                    {'error': 'No tiene permisos para pagar esta cuota'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except:
            return Response(
                {'error': 'Usuario no es residente'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar que la cuota esté pendiente
        if cuota_unidad.estado not in ['pendiente', 'vencida']:
            return Response(
                {'error': 'Solo se pueden pagar cuotas pendientes o vencidas'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generar ID único para el pago
        payment_id = str(uuid.uuid4())
        
        # Actualizar estado de la cuota
        cuota_unidad.estado = 'procesando'
        cuota_unidad.payment_id = payment_id
        cuota_unidad.payment_status = 'pending'
        cuota_unidad.save()
        
        # Datos para la pasarela
        payment_data = {
            'payment_id': payment_id,
            'amount': float(cuota_unidad.monto),
            'currency': 'BOB',
            'description': f'Cuota {cuota_unidad.cuota_mensual.mes_año} - Unidad {cuota_unidad.unidad.numero_casa}',
            'customer_info': {
                'name': f'{residente.persona.nombre} {residente.persona.apellido}',
                'email': residente.persona.email or 'residente@condominio.com',
            },
            'callback_url': f'/api/finanzas/cuotas-residente/{cuota_unidad.id}/confirmar-pago/',
            'return_url': f'/residente/cuotas/{cuota_unidad.id}/pago-exitoso/',
            'cancel_url': f'/residente/cuotas/{cuota_unidad.id}/pago-cancelado/'
        }
        
        # Integrar con la pasarela de pago real
        from .services import pasarela_service
        payment_response = pasarela_service.crear_pago(payment_data)
        
        if payment_response['success']:
            cuota_unidad.payment_url = payment_response['payment_url']
            cuota_unidad.save()
            payment_url = payment_response['payment_url']
        else:
            # Si falla la integración, revertir estado
            cuota_unidad.estado = 'pendiente'
            cuota_unidad.payment_id = None
            cuota_unidad.save()
            
            logger.error(f"Error creando pago en pasarela: {payment_response.get('error')}")
            return Response({
                'error': 'Error iniciando pago online',
                'details': payment_response.get('details', 'Error de conexión con la pasarela')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f"Pago iniciado por residente para cuota {cuota_unidad.id}, payment_id: {payment_id}")
        
        return Response({
            'message': 'Pago iniciado exitosamente',
            'payment_id': payment_id,
            'payment_url': payment_url,
            'amount': float(cuota_unidad.monto),
            'status': 'pending'
        })

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

# CU18 - Gestión de Ingresos
class IngresoViewSet(viewsets.ModelViewSet):
    """Gestión de Ingresos del Condominio - CU18"""
    queryset = Ingreso.objects.all()
    serializer_class = IngresoSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(registrado_por=self.request.user)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros opcionales
        tipo_ingreso = self.request.query_params.get('tipo_ingreso')
        estado = self.request.query_params.get('estado')
        mes_año = self.request.query_params.get('mes_año')
        unidad_id = self.request.query_params.get('unidad_id')
        
        if tipo_ingreso:
            queryset = queryset.filter(tipo_ingreso=tipo_ingreso)
        if estado:
            queryset = queryset.filter(estado=estado)
        if unidad_id:
            queryset = queryset.filter(unidad_relacionada_id=unidad_id)
        if mes_año:
            year, month = mes_año.split('-')
            queryset = queryset.filter(
                fecha_ingreso__year=year,
                fecha_ingreso__month=month
            )
        
        return queryset
    
    
    
    @action(detail=False, methods=['get'])
    def resumen_mensual(self, request):
        """Obtener resumen de ingresos por mes"""
        mes_año = request.query_params.get('mes_año')
        if not mes_año:
            mes_año = datetime.now().strftime('%Y-%m')
        
        year, month = mes_año.split('-')
        ingresos = self.get_queryset().filter(
            fecha_ingreso__year=year,
            fecha_ingreso__month=month,
            estado='confirmado'
        )
        
        # Crear o obtener resumen
        resumen, created = ResumenIngresos.objects.get_or_create(
            mes_año=mes_año,
            defaults={'creado_por': request.user}
        )
        
        # Recalcular totales
        resumen.calcular_totales()
        
        serializer = ResumenIngresosSerializer(resumen)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def confirmar_ingreso(self, request):
        """Confirmar un ingreso pendiente"""
        ingreso_id = request.data.get('ingreso_id')
        if not ingreso_id:
            return Response(
                {'error': 'Debe proporcionar ingreso_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ingreso = Ingreso.objects.get(id=ingreso_id)
            ingreso.estado = 'confirmado'
            ingreso.save()
            
            # Actualizar resumen del mes
            mes_año = ingreso.get_mes_año()
            resumen, created = ResumenIngresos.objects.get_or_create(
                mes_año=mes_año,
                defaults={'creado_por': request.user}
            )
            resumen.calcular_totales()
            
            serializer = self.get_serializer(ingreso)
            return Response(serializer.data)
            
        except Ingreso.DoesNotExist:
            return Response(
                {'error': 'Ingreso no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def cancelar_ingreso(self, request):
        """Cancelar un ingreso"""
        ingreso_id = request.data.get('ingreso_id')
        motivo = request.data.get('motivo', '')
        
        if not ingreso_id:
            return Response(
                {'error': 'Debe proporcionar ingreso_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ingreso = Ingreso.objects.get(id=ingreso_id)
            ingreso.estado = 'cancelado'
            if motivo:
                ingreso.observaciones += f"\nCancelado: {motivo}"
            ingreso.save()
            
            serializer = self.get_serializer(ingreso)
            return Response(serializer.data)
            
        except Ingreso.DoesNotExist:
            return Response(
                {'error': 'Ingreso no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class ResumenIngresosViewSet(viewsets.ReadOnlyModelViewSet):
    """Resúmenes de Ingresos - CU18"""
    queryset = ResumenIngresos.objects.all()
    serializer_class = ResumenIngresosSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def generar_resumen(self, request):
        """Generar resumen de ingresos para un mes específico"""
        mes_año = request.data.get('mes_año')
        if not mes_año:
            return Response(
                {'error': 'Debe proporcionar mes_año'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear o actualizar resumen
        resumen, created = ResumenIngresos.objects.get_or_create(
            mes_año=mes_año,
            defaults={'creado_por': request.user}
        )
        
        # Recalcular totales
        resumen.calcular_totales()
        
        serializer = self.get_serializer(resumen)
        return Response(serializer.data)