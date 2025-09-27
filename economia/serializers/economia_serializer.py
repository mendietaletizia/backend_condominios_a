from rest_framework import serializers
from economia.models import Gastos, Multa
# from finanzas.models import Pago, Expensa  # Comentado temporalmente

class GastosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gastos
        fields = '__all__'

class MultaSerializer(serializers.ModelSerializer):
    reglamento_info = serializers.SerializerMethodField()
    residente_info = serializers.SerializerMethodField()
    dias_vencido = serializers.SerializerMethodField()
    
    class Meta:
        model = Multa
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_modificacion']
    
    def get_reglamento_info(self, obj):
        """Obtener información del reglamento asociado"""
        if obj.reglamento:
            return {
                'id': obj.reglamento.id,
                'articulo': obj.reglamento.articulo,
                'titulo': obj.reglamento.titulo,
                'tipo': obj.reglamento.tipo,
                'monto_multa': obj.reglamento.monto_multa,
                'dias_suspension': obj.reglamento.dias_suspension
            }
        return None
    
    def get_residente_info(self, obj):
        """Obtener información del residente multado"""
        if obj.residente and obj.residente.persona:
            return {
                'id': obj.residente.id,
                'nombre': obj.residente.persona.nombre,
                'apellido': obj.residente.persona.apellido,
                'ci': obj.residente.persona.ci,
                'email': obj.residente.persona.email,
                'telefono': obj.residente.persona.telefono
            }
        return None
    
    def get_dias_vencido(self, obj):
        """Calcular días vencido si la multa está vencida"""
        try:
            if obj.estado == 'pendiente' and obj.fecha_vencimiento:
                from django.utils import timezone
                hoy = timezone.now().date()
                if obj.fecha_vencimiento < hoy:
                    return (hoy - obj.fecha_vencimiento).days
            return 0
        except:
            return 0

# Comentado temporalmente hasta que finanzas esté configurado
# Serializers comentados temporalmente para CU7
# class PagoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Pago
#         fields = '__all__'

# class ExpensaSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Expensa
#         fields = '__all__'
