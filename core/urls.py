from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnimalViewSet, EventViewSet, VaccineViewSet

router = DefaultRouter()
router.register(r'animals',AnimalViewSet)
router.register(r'events',EventViewSet)
router.register(r'vaccines',VaccineViewSet)

urlpatterns = [
     path('',include(router.urls))
]