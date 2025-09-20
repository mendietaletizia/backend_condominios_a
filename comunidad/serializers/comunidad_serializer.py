from rest_framework import serializers
from comunidad.models import Unidad, ResidentesUnidad, Evento, Notificacion, NotificacionResidente, Acta

class UnidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unidad
        fields = '__all__'

class ResidentesUnidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentesUnidad
        fields = '__all__'

class EventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evento
        fields = '__all__'

class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = '__all__'

class NotificacionResidenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificacionResidente
        fields = '__all__'

class ActaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Acta
        fields = '__all__'
