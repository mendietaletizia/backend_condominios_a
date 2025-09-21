from rest_framework import serializers
from mantenimiento.models import AreaComun, Reserva, Mantenimiento, BitacoraMantenimiento, Reglamento

class AreaComunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaComun
        fields = '__all__'

class ReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = '__all__'

class MantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mantenimiento
        fields = '__all__'

class BitacoraMantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BitacoraMantenimiento
        fields = '__all__'

class ReglamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reglamento
        fields = '__all__'
