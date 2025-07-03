from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from .models import Animal, Event, Vaccine

User = get_user_model()


class SyncUploadViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='pass')
    
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('upload')
        self.now = timezone.now()
        self.animal_id = "a0000000-0000-0000-0000-000000000000"
        self.event_id = "b0000000-0000-0000-0000-000000000000"
        self.vaccine_id = "c0000000-0000-0000-0000-000000000000"
        self.default_dob = "2020-01-01" 
        
    def test_create_new_animal(self):
        payload = {
            "pets": [{
                "id": self.animal_id,
                "name": "Bolt",
                "type": "Dog",
                "breed": "Husky",
                "date_of_birth": self.default_dob,
                "updated_at": self.now,
                "events": [],
                "vaccines": []
            }]
        }

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Animal.objects.count(), 1)
        animal = Animal.objects.get(id=self.animal_id)
        self.assertEqual(animal.name, "Bolt")
        self.assertEqual(animal.user, self.user)

    def test_update_animal_with_newer_data(self):
        animal = Animal.objects.create(
            id=self.animal_id,
            name="Antigo",
            type="Dog",
            breed="SRD",
            date_of_birth=self.default_dob,
            updated_at=self.now - timedelta(days=2),
            user=self.user
        )

        payload = {
            "pets": [{
                "id": animal.id,
                "name": "Atualizado",
                "type": "Gato",
                "breed": "Siames",
                "date_of_birth": "2019-01-01",
                "updated_at": self.now,
                "events": [],
                "vaccines": []
            }]
        }

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        animal.refresh_from_db()
        self.assertEqual(animal.name, "Atualizado")
        self.assertEqual(animal.type, "Gato")
        self.assertEqual(animal.breed, "Siames")

    def test_ignore_outdated_animal_data(self):
        animal = Animal.objects.create(
            id=self.animal_id,
            name="Rex",
            type="Dog",
            breed="Labrador",
            date_of_birth=self.default_dob,
            updated_at=self.now + timedelta(days=1),
            user=self.user
        )

        payload = {
            "pets": [{
                "id": animal.id,
                "name": "Should Not Update",
                "type": "Cat",
                "breed": "Persa",
                "date_of_birth": "2019-01-01",
                "updated_at": self.now - timedelta(days=1),
                "events": [],
                "vaccines": []
            }]
        }

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        animal.refresh_from_db()
        self.assertEqual(animal.name, "Rex")
        self.assertEqual(animal.type, "Dog")
        self.assertEqual(animal.breed, "Labrador")

    def test_create_new_event(self):
        animal = Animal.objects.create(
            id=self.animal_id,
            name="Rex",
            type="Dog",
            breed="Labrador",
            date_of_birth=self.default_dob,
            user=self.user,
            updated_at=self.now
        )

        animal.refresh_from_db()

        payload = {
            "pets": [{
                "id": animal.id,
                "name": animal.name,
                "type": animal.type,
                "breed": animal.breed,
                "date_of_birth": animal.date_of_birth,
                "updated_at": self.now,
                "events": [{
                    "id": self.event_id,
                    "type": "Consulta",
                    "date": "2023-01-01",
                    "observation": "Primeira consulta",
                    "updated_at": self.now
                }],
                "vaccines": []
            }]
        }

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Event.objects.count(), 1)
        event = Event.objects.get(id=self.event_id)
        self.assertEqual(event.type, "Consulta")
        self.assertEqual(event.animal, animal)

    def test_update_event_with_newer_data(self):
        animal = Animal.objects.create(
            id=self.animal_id,
            name="Rex",
            type="Dog",
            breed="Labrador",
            date_of_birth=self.default_dob,
            user=self.user,
            updated_at=self.now
        )
        
        event = Event.objects.create(
            id=self.event_id,
            type="Consulta",
            date="2023-01-01",
            observation="Original",
            updated_at=self.now - timedelta(days=1),
            animal=animal
        )

        payload = {
            "pets": [{
                "id": animal.id,
                "name": animal.name,
                "type": animal.type,
                "breed": animal.breed,
                "date_of_birth": animal.date_of_birth,
                "updated_at": self.now,
                "events": [{
                    "id": event.id,
                    "type": "Cirurgia",
                    "date": "2023-02-01",
                    "observation": "Atualizado",
                    "updated_at": self.now
                }],
                "vaccines": []
            }]
        }

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event.refresh_from_db()
        self.assertEqual(event.type, "Cirurgia")
        self.assertEqual(event.observation, "Atualizado")
        self.assertEqual(event.date.strftime("%Y-%m-%d"), "2023-02-01")

    def test_ignore_outdated_event_data(self):
        animal = Animal.objects.create(
            id=self.animal_id,
            name="Rex",
            type="Dog",
            breed="Labrador",
            date_of_birth=self.default_dob,
            user=self.user,
            updated_at=self.now
        )
        
        event = Event.objects.create(
            id=self.event_id,
            type="Consulta",
            date="2023-01-01",
            observation="Original",
            updated_at=self.now + timedelta(hours=1),
            animal=animal
        )

        payload = {
            "pets": [{
                "id": animal.id,
                "name": animal.name,
                "type": animal.type,
                "breed": animal.breed,
                "date_of_birth": animal.date_of_birth,
                "updated_at": self.now,
                "events": [{
                    "id": event.id,
                    "type": "Desatualizado",
                    "date": "2020-01-01",
                    "observation": "Tentativa de overwrite",
                    "updated_at": self.now
                }],
                "vaccines": []
            }]
        }

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event.refresh_from_db()
        self.assertEqual(event.type, "Consulta")
        self.assertEqual(event.observation, "Original")
        self.assertEqual(event.date.strftime("%Y-%m-%d"), "2023-01-01")

    def test_create_new_vaccine(self):
        animal = Animal.objects.create(
            id=self.animal_id,
            name="Rex",
            type="Dog",
            breed="Labrador",
            date_of_birth=self.default_dob,
            user=self.user,
            updated_at=self.now
        )

        animal.refresh_from_db()

        payload = {
            "pets": [{
                "id": animal.id,
                "name": animal.name,
                "type": animal.type,
                "breed": animal.breed,
                "date_of_birth": animal.date_of_birth,
                "updated_at": self.now,
                "events": [],
                "vaccines": [{
                    "id": self.vaccine_id,
                    "name": "V10",
                    "application_date": "2023-01-01",
                    "next_dose_date": "2024-01-01",
                    "updated_at": self.now
                }]
            }]
        }

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Vaccine.objects.count(), 1)
        vaccine = Vaccine.objects.get(id=self.vaccine_id)
        self.assertEqual(vaccine.name, "V10")
        self.assertEqual(vaccine.animal, animal)
        

    def test_update_vaccine_with_newer_data(self):
        animal = Animal.objects.create(
            id=self.animal_id,
            name="Rex",
            type="Dog",
            breed="Labrador",
            date_of_birth=self.default_dob,
            user=self.user,
            updated_at=self.now
        )

        vaccine = Vaccine.objects.create(
            id=self.vaccine_id,
            name="V10",
            application_date="2023-01-01",
            next_dose_date="2024-01-01",
            updated_at=self.now - timedelta(days=1),
            animal=animal
        )

        payload = {
            "pets": [{
                "id": animal.id,
                "name": animal.name,
                "type": animal.type,
                "breed": animal.breed,
                "date_of_birth": animal.date_of_birth,
                "updated_at": self.now,
                "events": [],
                "vaccines": [{
                    "id": vaccine.id,
                    "name": "V8",
                    "application_date": "2023-02-01",
                    "next_dose_date": "2024-02-01",
                    "updated_at": self.now
                }]
            }]
        }

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vaccine.refresh_from_db()
        self.assertEqual(vaccine.name, "V8")
        self.assertEqual(vaccine.application_date.strftime("%Y-%m-%d"), "2023-02-01")
        self.assertEqual(vaccine.next_dose_date.strftime("%Y-%m-%d"), "2024-02-01")

    def test_ignore_outdated_vaccine_data(self):
        animal = Animal.objects.create(
            id=self.animal_id,
            name="Rex",
            type="Dog",
            breed="Labrador",
            date_of_birth=self.default_dob,
            user=self.user,
            updated_at=self.now
        )
        
        vaccine = Vaccine.objects.create(
            id=self.vaccine_id,
            name="V10",
            application_date="2023-01-01",
            next_dose_date="2024-01-01",
            updated_at=self.now + timedelta(hours=1),
            animal=animal
        )

        payload = {
            "pets": [{
                "id": animal.id,
                "name": animal.name,
                "type": animal.type,
                "breed": animal.breed,
                "date_of_birth": animal.date_of_birth,
                "updated_at": self.now,
                "events": [],
                "vaccines": [{
                    "id": vaccine.id,
                    "name": "Desatualizada",
                    "application_date": "2020-01-01",
                    "next_dose_date": "2021-01-01",
                    "updated_at": self.now
                }]
            }]
        }

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vaccine.refresh_from_db()
        self.assertEqual(vaccine.name, "V10")
        self.assertEqual(vaccine.application_date.strftime("%Y-%m-%d"), "2023-01-01")
        self.assertEqual(vaccine.next_dose_date.strftime("%Y-%m-%d"), "2024-01-01")