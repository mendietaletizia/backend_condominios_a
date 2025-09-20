from rest_framework import serializers
from economia.models import Gastos, Multa
from finanzas.models import Pago, Expensa

class GastosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gastos
        fields = '__all__'

class MultaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Multa
        fields = '__all__'

class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__'

class ExpensaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expensa
        fields = '__all__'
