from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnimalViewSet, EventViewSet, VaccineViewSet, SyncUploadView,SyncDownloadView, SyncCheckUpdatesView

router = DefaultRouter()
router.register(r'animals',AnimalViewSet)
router.register(r'events',EventViewSet)
router.register(r'vaccines',VaccineViewSet)

urlpatterns = [
     path('',include(router.urls)),
     path('sync/upload',SyncUploadView.as_view(),name='upload'),
     path('sync/download',SyncDownloadView.as_view(),name='download'),
     path('sync/check-update',SyncCheckUpdatesView.as_view(),name='check_update')
]