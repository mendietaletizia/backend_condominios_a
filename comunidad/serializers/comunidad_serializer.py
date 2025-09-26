from rest_framework import serializers
from comunidad.models import Unidad, ResidentesUnidad, Evento, Notificacion, NotificacionResidente, Acta, Mascota
from mantenimiento.models import AreaComun
from usuarios.models import Residentes, Usuario, PlacaVehiculo

class UnidadSerializer(serializers.ModelSerializer):
    residentes_info = serializers.SerializerMethodField()
    mascotas_info = serializers.SerializerMethodField()
    vehiculos_info = serializers.SerializerMethodField()
    total_residentes_real = serializers.SerializerMethodField()
    total_mascotas_real = serializers.SerializerMethodField()
    total_vehiculos_real = serializers.SerializerMethodField()
    
    class Meta:
        model = Unidad
        fields = '__all__'
    
    def get_residentes_info(self, obj):
        """Obtener información detallada de residentes asociados"""
        relaciones = obj.residentesunidad_set.filter(estado=True)
        return [
            {
                'id': rel.id,
                'residente_id': rel.id_residente.id,
                'residente_nombre': rel.id_residente.persona.nombre if rel.id_residente.persona else 'Sin nombre',
                'residente_ci': rel.id_residente.persona.ci if rel.id_residente.persona else 'Sin CI',
                'residente_email': rel.id_residente.persona.email if rel.id_residente.persona else 'Sin email',
                'residente_telefono': rel.id_residente.persona.telefono if rel.id_residente.persona else 'Sin teléfono',
                'rol_en_unidad': rel.rol_en_unidad,
                'fecha_inicio': rel.fecha_inicio,
                'fecha_fin': rel.fecha_fin,
                'estado': rel.estado
            }
            for rel in relaciones
        ]
    
    def get_mascotas_info(self, obj):
        """Obtener información detallada de mascotas asociadas"""
        mascotas = obj.mascota_set.filter(activo=True)
        return [
            {
                'id': mascota.id,
                'nombre': mascota.nombre,
                'tipo': mascota.tipo,
                'raza': mascota.raza,
                'color': mascota.color,
                'fecha_nacimiento': mascota.fecha_nacimiento,
                'observaciones': mascota.observaciones,
                'residente_id': mascota.residente.id,
                'residente_nombre': mascota.residente.persona.nombre if mascota.residente.persona else 'Sin nombre',
                'fecha_registro': mascota.fecha_registro,
                'activo': mascota.activo
            }
            for mascota in mascotas
        ]
    
    def get_vehiculos_info(self, obj):
        """Obtener información de vehículos asociados a través de residentes"""
        try:
            vehiculos = PlacaVehiculo.objects.filter(
                residente__residentesunidad__id_unidad=obj,
                residente__residentesunidad__estado=True,
                activo=True
            ).distinct()
            
            return [
                {
                    'id': vehiculo.id,
                    'placa': vehiculo.placa,
                    'marca': vehiculo.marca,
                    'modelo': vehiculo.modelo,
                    'color': vehiculo.color,
                    'residente_id': vehiculo.residente.id,
                    'residente_nombre': vehiculo.residente.persona.nombre if vehiculo.residente.persona else 'Sin nombre',
                    'fecha_registro': vehiculo.fecha_registro,
                    'activo': vehiculo.activo
                }
                for vehiculo in vehiculos
            ]
        except Exception as e:
            # Si hay algún error, retornar lista vacía
            return []
    
    def get_total_residentes_real(self, obj):
        """Obtener el número real de residentes activos"""
        return obj.residentesunidad_set.filter(estado=True).count()
    
    def get_total_mascotas_real(self, obj):
        """Obtener el número real de mascotas activas"""
        return obj.mascota_set.filter(activo=True).count()
    
    def get_total_vehiculos_real(self, obj):
        """Obtener el número real de vehículos activos"""
        try:
            return PlacaVehiculo.objects.filter(
                residente__residentesunidad__id_unidad=obj,
                residente__residentesunidad__estado=True,
                activo=True
            ).distinct().count()
        except Exception as e:
            return 0

class ResidentesUnidadSerializer(serializers.ModelSerializer):
    residente_info = serializers.SerializerMethodField()
    unidad_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ResidentesUnidad
        fields = '__all__'
    
    def _resolve_fk(self, model_cls, value, field_label):
        """Accepts an int PK, string PK, dict with id/pk, or a model instance."""
        try:
            # Already a proper instance
            if isinstance(value, model_cls):
                return value
            # Dict coming from frontend like { id: 1, ... }
            if isinstance(value, dict):
                candidate = value.get('id') or value.get('pk')
                if candidate is None:
                    raise serializers.ValidationError({field_label: 'Debe incluir id en el objeto enviado.'})
                value = candidate
            # Strings containing numbers
            if isinstance(value, str):
                if value.isdigit():
                    value = int(value)
                else:
                    raise serializers.ValidationError({field_label: 'Formato inválido. Envíe un ID numérico o un objeto con id.'})
            # Integers (primary key)
            if isinstance(value, int):
                return model_cls.objects.get(pk=value)
            # Anything else is invalid
            raise serializers.ValidationError({field_label: 'Valor inválido para relación.'})
        except model_cls.DoesNotExist:
            raise serializers.ValidationError({field_label: 'No existe el registro especificado.'})

    def validate(self, attrs):
        """Normalize foreign keys if raw payload sent nested objects or strings."""
        data = {**getattr(self, 'initial_data', {}), **attrs}
        # id_residente
        if 'id_residente' in self.initial_data:
            attrs['id_residente'] = self._resolve_fk(Residentes, self.initial_data.get('id_residente'), 'id_residente')
        # id_unidad
        if 'id_unidad' in self.initial_data:
            attrs['id_unidad'] = self._resolve_fk(Unidad, self.initial_data.get('id_unidad'), 'id_unidad')
        return super().validate(attrs)

    def create(self, validated_data):
        # Safety net if values slipped through without normalization
        if not isinstance(validated_data.get('id_residente'), Residentes) and 'id_residente' in self.initial_data:
            validated_data['id_residente'] = self._resolve_fk(Residentes, self.initial_data.get('id_residente'), 'id_residente')
        if not isinstance(validated_data.get('id_unidad'), Unidad) and 'id_unidad' in self.initial_data:
            validated_data['id_unidad'] = self._resolve_fk(Unidad, self.initial_data.get('id_unidad'), 'id_unidad')
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'id_residente' in self.initial_data:
            validated_data['id_residente'] = self._resolve_fk(Residentes, self.initial_data.get('id_residente'), 'id_residente')
        if 'id_unidad' in self.initial_data:
            validated_data['id_unidad'] = self._resolve_fk(Unidad, self.initial_data.get('id_unidad'), 'id_unidad')
        return super().update(instance, validated_data)

    def get_residente_info(self, obj):
        if obj.id_residente and obj.id_residente.persona:
            return {
                'id': obj.id_residente.id,
                'nombre': obj.id_residente.persona.nombre,
                'ci': obj.id_residente.persona.ci,
                'email': obj.id_residente.persona.email
            }
        return None
    
    def get_unidad_info(self, obj):
        if obj.id_unidad:
            return {
                'id': obj.id_unidad.id,
                'numero_casa': obj.id_unidad.numero_casa,
                'metros_cuadrados': obj.id_unidad.metros_cuadrados
            }
        return None

class EventoSerializer(serializers.ModelSerializer):
    areas_info = serializers.SerializerMethodField()
    class Meta:
        model = Evento
        fields = '__all__'

    def get_areas_info(self, obj):
        try:
            return [
                { 'id': a.id, 'nombre': a.nombre, 'tipo': a.tipo }
                for a in obj.areas.all()
            ]
        except Exception:
            return []

    def create(self, validated_data):
        areas_ids = None
        if hasattr(self, 'initial_data'):
            areas_ids = self.initial_data.get('areas')
        evento = super().create(validated_data)
        if isinstance(areas_ids, list):
            from mantenimiento.models import AreaComun
            qs = AreaComun.objects.filter(id__in=areas_ids)
            evento.areas.set(qs)
        return evento

    def update(self, instance, validated_data):
        areas_ids = None
        if hasattr(self, 'initial_data'):
            areas_ids = self.initial_data.get('areas')
        evento = super().update(instance, validated_data)
        if isinstance(areas_ids, list):
            from mantenimiento.models import AreaComun
            qs = AreaComun.objects.filter(id__in=areas_ids)
            evento.areas.set(qs)
        return evento

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

class MascotaSerializer(serializers.ModelSerializer):
    residente_info = serializers.SerializerMethodField()
    unidad_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Mascota
        fields = '__all__'
    
    def get_residente_info(self, obj):
        if obj.residente and obj.residente.persona:
            return {
                'id': obj.residente.id,
                'nombre': obj.residente.persona.nombre,
                'ci': obj.residente.persona.ci,
                'email': obj.residente.persona.email
            }
        return None
    
    def get_unidad_info(self, obj):
        if obj.unidad:
            return {
                'id': obj.unidad.id,
                'numero_casa': obj.unidad.numero_casa,
                'metros_cuadrados': obj.unidad.metros_cuadrados
            }
        return None
