from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiTypes
from django.db.models import Q
from .models import Animal, Event, Vaccine
from .serializers import AnimalSerializer, EventSerializer, VaccineSerializer, SyncUploadRequestSerializer, SyncDownloadRequestSerializer, SyncDownloadResponseSerializer


@extend_schema(tags=['Animais'])
class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer

    def get_queryset(self):
        return Animal.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_at=now())


@extend_schema(tags=['Eventos'])
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def get_queryset(self):
        return Event.objects.filter(animal__user=self.request.user)

@extend_schema(tags=['Vacinas'])
class VaccineViewSet(viewsets.ModelViewSet):
    queryset  = Vaccine.objects.all()
    serializer_class = VaccineSerializer

    def get_queryset(self):
        return Vaccine.objects.filter(animal__user=self.request.user)


@extend_schema(
    request=SyncUploadRequestSerializer,  
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
    tags=["Sincronização"],
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


@extend_schema(
    request=SyncDownloadRequestSerializer,
    responses=SyncDownloadResponseSerializer,
    tags=["Sincronização"],
    description="Retorna os animais com eventos e vacinas alterados após a data de sincronização enviada.",
    examples=[
        OpenApiExample(
            name="Requisição com 'last_synced_at'",
            description="Baixa apenas os dados alterados após o timestamp informado.",
            value={
                "last_synced_at": "2025-07-03T12:00:00Z"
            },
            request_only=True
        ),
        OpenApiExample(
            name="Requisição sem 'last_synced_at'",
            description="Baixa **todos** os dados disponíveis, como numa primeira sincronização.",
            value={},
            request_only=True
        )
    ]
)
class SyncDownloadView(APIView):
    permission_classes = [IsAuthenticated]


    def post(self, request):
        serializer = SyncDownloadRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        last_synced_at = serializer.validated_data.get('last_synced_at')
        pets_qs = Animal.objects.filter(user=request.user)
        
        if last_synced_at:
            pets_qs = pets_qs.filter(
                Q(updated_at__gt=last_synced_at) |
                Q(events__updated_at__gt=last_synced_at) |
                Q(vaccines__updated_at__gt=last_synced_at)
            ).distinct()

        now_sync = now()

        response_serializer = SyncDownloadResponseSerializer({
            'pets': pets_qs,
            'synced_at': now_sync
        })
        return Response(response_serializer.data)
    

@extend_schema(
    request=SyncDownloadRequestSerializer,
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT
    },
    examples=[
        OpenApiExample(
            name="Exemplo de resposta com atualizações",
            value={
                "has_updates": True,
                "update_counts": {
                    "animals": 3,
                    "events": 5,
                    "vaccines": 2
                }
            },
            response_only=True
        ),
        OpenApiExample(
            name="Exemplo sem atualizações",
            value={
                "has_updates": False,
                "update_counts": {
                    "animals": 0,
                    "events": 0,
                    "vaccines": 0
                }
            },
            response_only=True
        ),
        OpenApiExample(
            name="Requisição com `last_synced_at`",
            value={
                "last_synced_at": "2025-07-03T12:00:00Z"
            },
            request_only=True
        )
    ],
    tags=["Sincronização"],
    description="Verifica se existem animais, eventos ou vacinas que foram atualizados após a última sincronização."
)
class SyncCheckUpdatesView(APIView):
    permission_classes = [IsAuthenticated]


    def post(self, request):
        serializer = SyncDownloadRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        last_synced_at = serializer.validated_data.get('last_synced_at')
        user = request.user

        animals_qs = Animal.objects.filter(user=user)
        events_qs = Event.objects.filter(animal__user=user)
        vaccines_qs = Vaccine.objects.filter(animal__user=user)

        if last_synced_at:
            animals_qs = animals_qs.filter(updated_at__gt=last_synced_at)
            events_qs = events_qs.filter(updated_at__gt=last_synced_at)
            vaccines_qs = vaccines_qs.filter(updated_at__gt=last_synced_at)

        animal_count = animals_qs.count()
        event_count = events_qs.count()
        vaccine_count = vaccines_qs.count()

        has_updates = any([animal_count, event_count, vaccine_count])

        return Response({
            "has_updates": has_updates,
            "update_counts": {
                "animals": animal_count,
                "events": event_count,
                "vaccines": vaccine_count
            }
        })