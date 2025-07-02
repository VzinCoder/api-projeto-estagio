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
        fields = '__all__'
