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
