from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from .models import Animal, Event, Vaccine
import uuid

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


class SyncDownloadViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass'
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('download')
        
        self.animal1 = Animal.objects.create(
            id=uuid.uuid4(),
            user=self.user,
            name="Buddy",
            type="Dog",
            breed="Golden Retriever",
            date_of_birth="2019-05-15",
            updated_at=timezone.now() - timedelta(days=2)
        )
        
        self.animal2 = Animal.objects.create(
            id=uuid.uuid4(),
            user=self.user,
            name="Whiskers",
            type="Cat",
            breed="Siamese",
            date_of_birth="2020-03-10",
            updated_at=timezone.now()
        )
        
        self.event1 = Event.objects.create(
            animal=self.animal1,
            type="VET_VISIT",
            date="2023-10-01",
            updated_at=timezone.now() - timedelta(days=1)
        )
        
        self.vaccine1 = Vaccine.objects.create(
            animal=self.animal1,
            name="Rabies",
            application_date="2023-09-15",
            updated_at=timezone.now()
        )
    
    def test_unauthenticated_access(self):
        self.client.logout()
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_download_all_data_without_timestamp(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(len(data['pets']), 2)
        self.assertIsNotNone(data['synced_at'])
        
        animal1_data = next(a for a in data['pets'] if a['id'] == str(self.animal1.id))
        self.assertEqual(len(animal1_data['events']), 1)
        self.assertEqual(len(animal1_data['vaccines']), 1)
    
    def test_download_only_recent_changes(self):
        last_sync = timezone.now() - timedelta(hours=24)
        
        response = self.client.post(self.url, {
            'last_synced_at': last_sync.isoformat()
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(len(data['pets']), 2)
        
        animal_ids = [a['id'] for a in data['pets']]
        self.assertIn(str(self.animal1.id), animal_ids)
    
    def test_download_excludes_old_records(self):
        old_vaccine_time = timezone.now() - timedelta(days=2)
        Vaccine.objects.filter(animal=self.animal1).update(updated_at=old_vaccine_time)
    
        old_event_time = timezone.now() - timedelta(days=2)
        Event.objects.filter(animal=self.animal1).update(updated_at=old_event_time)

        last_sync = timezone.now() - timedelta(hours=1)
    
        response = self.client.post(self.url, {
            'last_synced_at': last_sync.isoformat()
        }, format='json')
    
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
    
        self.assertEqual(len(data['pets']), 1)
        self.assertEqual(data['pets'][0]['id'], str(self.animal2.id))
    
    def test_download_handles_empty_changes(self):
        last_sync = timezone.now() + timedelta(hours=1)
        
        response = self.client.post(self.url, {
            'last_synced_at': last_sync.isoformat()
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['pets']), 0)

class SyncCheckUpdatesViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass'
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('check_update')
        
        self.animal = Animal.objects.create(
            user=self.user,
            name="Max",
            type="Dog",
            breed="Labrador",
            date_of_birth="2018-11-20",
            updated_at=timezone.now() - timedelta(days=3)
        )
        
        self.event = Event.objects.create(
            animal=self.animal,
            type="GROOMING",
            date="2023-10-05",
            updated_at=timezone.now() - timedelta(days=2)
        )
        
        self.vaccine = Vaccine.objects.create(
            animal=self.animal,
            name="Parvovirus",
            application_date="2023-09-20",
            updated_at=timezone.now() - timedelta(days=1)
        )
    
    def test_unauthenticated_access(self):
        self.client.logout()
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_check_without_timestamp(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertTrue(data['has_updates'])
        self.assertEqual(data['update_counts']['animals'], 1)
        self.assertEqual(data['update_counts']['events'], 1)
        self.assertEqual(data['update_counts']['vaccines'], 1)
    
    def test_check_with_recent_timestamp(self):
        last_sync = timezone.now() - timedelta(hours=1)
        
        response = self.client.post(self.url, {
            'last_synced_at': last_sync.isoformat()
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        
        self.assertFalse(data['has_updates'])
        self.assertEqual(data['update_counts']['animals'], 0)
        self.assertEqual(data['update_counts']['events'], 0)
        self.assertEqual(data['update_counts']['vaccines'], 0)
    
    def test_check_with_partial_updates(self):
        new_event = Event.objects.create(
            animal=self.animal,
            type="TRAINING",
            date="2023-10-10",
            updated_at=timezone.now()
        )
        
        last_sync = timezone.now() - timedelta(hours=12)
        
        response = self.client.post(self.url, {
            'last_synced_at': last_sync.isoformat()
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        
        self.assertTrue(data['has_updates'])
        self.assertEqual(data['update_counts']['animals'], 0)
        self.assertEqual(data['update_counts']['events'], 1)
        self.assertEqual(data['update_counts']['vaccines'], 0)
    
    def test_check_with_multiple_updates(self):
        self.animal.name = "Max Updated"
        self.animal.updated_at = timezone.now()
        self.animal.save()
        
        self.vaccine.next_dose_date = "2024-09-20"
        self.vaccine.updated_at = timezone.now()
        self.vaccine.save()
        
        last_sync = timezone.now() - timedelta(hours=1)
        
        response = self.client.post(self.url, {
            'last_synced_at': last_sync.isoformat()
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        
        self.assertTrue(data['has_updates'])
        self.assertEqual(data['update_counts']['animals'], 1)
        self.assertEqual(data['update_counts']['events'], 0)
        self.assertEqual(data['update_counts']['vaccines'], 1)