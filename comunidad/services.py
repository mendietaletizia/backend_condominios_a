from django.utils import timezone
from django.db import transaction
from .models import Notificacion, NotificacionResidente
from usuarios.models import Residentes

class NotificacionService:
    """Servicio para gestionar notificaciones automáticas"""
    
    @staticmethod
    def crear_notificacion_cuota(cuota_mensual, cuotas_unidad):
        """Crear notificación automática para cuotas mensuales"""
        try:
            with transaction.atomic():
                # Calcular monto por unidad
                monto_por_unidad = cuota_mensual.calcular_monto_por_unidad()
                
                # Crear notificación principal
                notificacion = Notificacion.objects.create(
                    titulo=f"💰 Nueva Cuota Mensual - {cuota_mensual.mes_año}",
                    contenido=f"""
🏠 <strong>CUOTA MENSUAL GENERADA</strong>

📅 <strong>Período:</strong> {cuota_mensual.mes_año}
💰 <strong>Monto por unidad:</strong> Bs. {monto_por_unidad:,.2f}
📆 <strong>Fecha límite de pago:</strong> {cuota_mensual.fecha_limite}

📝 <strong>Descripción:</strong>
{cuota_mensual.descripcion or 'Cuota mensual de mantenimiento y gastos comunes'}

⚠️ <strong>Importante:</strong>
• El pago debe realizarse antes de la fecha límite
• Puede pagar en efectivo, transferencia o cheque
• Presente su comprobante en la administración
• En caso de retraso, se aplicarán recargos según el reglamento

📞 <strong>Contacto:</strong> Administración del condominio
                    """,
                    fecha=timezone.now(),
                    tipo='cuota',
                    prioridad='alta',
                    enviar_a_todos=False
                )
                
                # Enviar a residentes específicos
                residentes_notificados = 0
                for cuota_unidad in cuotas_unidad:
                    if cuota_unidad.unidad.residentes.exists():
                        residentes = cuota_unidad.unidad.residentes.filter(estado=True)
                        for residente_unidad in residentes:
                            NotificacionResidente.objects.create(
                                notificacion=notificacion,
                                residente=residente_unidad.id_residente
                            )
                            residentes_notificados += 1
                
                print(f"Notificación de cuota enviada a {residentes_notificados} residentes")
                return notificacion
        except Exception as e:
            print(f"Error creando notificación de cuota: {e}")
            return None
    
    @staticmethod
    def crear_notificacion_multa(multa):
        """Crear notificación automática para multas"""
        try:
            with transaction.atomic():
                notificacion = Notificacion.objects.create(
                    titulo=f"Multa Aplicada - {multa.reglamento.articulo if multa.reglamento else 'Sin artículo'}",
                    contenido=f"""
                    Se le ha aplicado una multa por incumplimiento del reglamento.
                    
                    Motivo: {multa.motivo}
                    Monto: Bs. {multa.monto:,.2f}
                    Fecha de emisión: {multa.fecha_emision}
                    Fecha límite de pago: {multa.fecha_vencimiento}
                    
                    {multa.observaciones or ''}
                    
                    Por favor, acérquese a la administración para regularizar su situación.
                    """,
                    fecha=timezone.now(),
                    tipo='multa',
                    prioridad='urgente',
                    enviar_a_todos=False
                )
                
                # Enviar solo al residente específico
                NotificacionResidente.objects.create(
                    notificacion=notificacion,
                    residente=multa.residente
                )
                
                return notificacion
        except Exception as e:
            print(f"Error creando notificación de multa: {e}")
            return None
    
    @staticmethod
    def crear_notificacion_general(titulo, contenido, tipo='comunicado', prioridad='media', residentes_ids=None):
        """Crear notificación general"""
        try:
            with transaction.atomic():
                notificacion = Notificacion.objects.create(
                    titulo=titulo,
                    contenido=contenido,
                    fecha=timezone.now(),
                    tipo=tipo,
                    prioridad=prioridad,
                    enviar_a_todos=residentes_ids is None
                )
                
                if residentes_ids:
                    # Enviar a residentes específicos
                    for residente_id in residentes_ids:
                        NotificacionResidente.objects.create(
                            notificacion=notificacion,
                            residente_id=residente_id
                        )
                else:
                    # Enviar a todos los residentes
                    residentes = Residentes.objects.filter(activo=True)
                    for residente in residentes:
                        NotificacionResidente.objects.create(
                            notificacion=notificacion,
                            residente=residente
                        )
                
                return notificacion
        except Exception as e:
            print(f"Error creando notificación general: {e}")
            return None
