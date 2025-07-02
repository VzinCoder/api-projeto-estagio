from django.shortcuts import render
from rest_framework import viewsets
from .models import Animal, Event, Vaccine
from .serializers import AnimalSerializer, EventSerializer, VaccineSerializer


class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class VaccineViewSet(viewsets.ModelViewSet):
    queryset  = Vaccine.objects.all()
    serializer_class = VaccineSerializer



