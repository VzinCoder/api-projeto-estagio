from rest_framework import viewsets, status,serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter, OpenApiTypes
from .models import Animal, Event, Vaccine
from .serializers import AnimalSerializer, EventSerializer, VaccineSerializer, SyncUploadRequestSerializer

class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer


    def perform_update(self, serializer):
        serializer.save(updated_at=now())


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class VaccineViewSet(viewsets.ModelViewSet):
    queryset  = Vaccine.objects.all()
    serializer_class = VaccineSerializer



@extend_schema(
    request=SyncUploadRequestSerializer,  
    responses={200: OpenApiTypes.STR},
    examples=[
        OpenApiExample(
            'Exemplo completo de sincronização',
            value={
                "pets": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Rex",
                        "type": "Cachorro",
                        "breed": "Labrador",
                        "date_of_birth": "2020-05-15",
                        "updated_at": "2023-10-25T14:30:00Z",
                        "events": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440001",
                                "type": "Consulta veterinária",
                                "date": "2023-10-10",
                                "observation": "Check-up anual",
                                "updated_at": "2023-10-10T09:15:00Z"
                            },
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440002",
                                "type": "Vacinação",
                                "date": "2023-10-15",
                                "updated_at": "2023-10-15T11:20:00Z"
                            }
                        ],
                        "vaccines": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440003",
                                "name": "Antirrábica",
                                "application_date": "2023-10-15",
                                "next_dose_date": "2024-10-15",
                                "updated_at": "2023-10-15T11:20:00Z"
                            },
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440004",
                                "name": "V8",
                                "application_date": "2023-09-20",
                                "updated_at": "2023-09-20T10:00:00Z"
                            }
                        ]
                    },
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440005",
                        "name": "Mimi",
                        "type": "Gato",
                        "breed": "Siamês",
                        "date_of_birth": "2021-02-28",
                        "updated_at": "2023-10-20T16:45:00Z",
                        "events": [],
                        "vaccines": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440006",
                                "name": "V4",
                                "application_date": "2023-10-05",
                                "next_dose_date": "2024-10-05",
                                "updated_at": "2023-10-05T14:00:00Z"
                            }
                        ]
                    }
                ]
            },
            request_only=True,
            status_codes=['200']
        )
    ],
    description="Sincroniza os dados do aplicativo com o servidor, atualizando apenas se `updated_at` for mais recente."
)
class SyncUploadView(APIView):
    permission_classes = [IsAuthenticated]


    def post(self,request):
        user = request.user
        serializer = SyncUploadRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pets = serializer.validated_data['pets']
        for pet_data in pets:
            pet_id = pet_data.get('id', None)
            events = pet_data.pop('events', [])
            vaccines = pet_data.pop('vaccines', [])
            updated_at_incoming = pet_data.get('updated_at')

            try:
                pet_obj = Animal.objects.get(id=pet_id,user=user)
                if updated_at_incoming > pet_obj.updated_at:
                    for attr, value in pet_data.items():
                        setattr(pet_obj, attr, value)
                    pet_obj.updated_at = updated_at_incoming
                    pet_obj.save()    
            except Animal.DoesNotExist:
                pet_data['user'] = user
                pet_data['updated_at'] = updated_at_incoming
                pet_obj = Animal.objects.create(**pet_data)
            
            for event in events:
                event_id = event.get('id',None)            
                event_updated_at = event.get('updated_at')
                try:
                    event_obj = Event.objects.get(id=event_id,animal=pet_obj)
                    if event_updated_at > event_obj.updated_at:
                        for attr, value in event.items():
                            setattr(event_obj,attr,value)
                        event_obj.updated_at = event_updated_at
                        event_obj.save()
                except Event.DoesNotExist:
                    event['animal'] = pet_obj
                    event['updated_at'] = event_updated_at
                    Event.objects.create(**event)
            
            for vaccine in vaccines:
                vaccine_id = vaccine.get('id')
                vaccine_updated_at = vaccine.get('updated_at')
                try:
                    vaccine_obj = Vaccine.objects.get(id=vaccine_id,animal=pet_obj)
                    if vaccine_updated_at > vaccine_obj.updated_at:
                        for attr, value in vaccine.items():
                            setattr(vaccine_obj,attr,value)
                        vaccine_obj.updated_at = vaccine_updated_at
                        vaccine_obj.save()
                except Vaccine.DoesNotExist:
                    vaccine['animal'] = pet_obj
                    vaccine['updated_at'] = vaccine_updated_at
                    Vaccine.objects.create(**vaccine)

        return Response(status=status.HTTP_200_OK)



