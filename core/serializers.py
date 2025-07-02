from rest_framework import serializers
from .models import Animal,Vaccine,Event

class VaccineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vaccine
        fields = '__all__'


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'


class AnimalSerializer(serializers.ModelSerializer):
    events = EventSerializer(many=True, read_only=True)
    vaccines = VaccineSerializer(many=True, read_only=True)
    class Meta:
        model = Animal
        exclude = ['user']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('user', None)
        return super().update(instance, validated_data)

class EventUploadSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    type = serializers.CharField()
    date = serializers.DateField()
    observation = serializers.CharField(allow_blank=True, required=False)
    updated_at = serializers.DateTimeField()


class VaccineUploadSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    application_date = serializers.DateField()
    next_dose_date = serializers.DateField(required=False)
    updated_at = serializers.DateTimeField()


class AnimalUploadSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    type = serializers.CharField()
    breed = serializers.CharField()
    date_of_birth = serializers.DateField()
    updated_at = serializers.DateTimeField()
    events = EventUploadSerializer(many=True, required=False)
    vaccines = VaccineUploadSerializer(many=True, required=False)

class SyncUploadRequestSerializer(serializers.Serializer):
    pets = AnimalUploadSerializer(many=True)