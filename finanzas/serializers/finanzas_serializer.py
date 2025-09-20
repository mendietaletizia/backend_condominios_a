from rest_framework import serializers
from finanzas.models import Expensa, Pago

class ExpensaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expensa
        fields = '__all__'

class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__'
