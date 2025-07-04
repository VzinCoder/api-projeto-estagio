import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now
# Create your models here.

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    updated_at = models.DateTimeField(default=now)
    class Meta:
        abstract = True 

class Animal(BaseModel):
    user = models.ForeignKey(get_user_model(),on_delete=models.CASCADE, related_name='animals')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    breed = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    
    def __str__(self):
        return self.name
    
class Vaccine(BaseModel):
    animal = models.ForeignKey(Animal,on_delete=models.CASCADE,related_name='vaccines')
    name = models.CharField(max_length=100)
    application_date = models.DateField()
    next_dose_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.animal.name}"


class Event(BaseModel):
    animal = models.ForeignKey(Animal,on_delete=models.CASCADE,related_name='events')
    type = models.CharField(max_length=100)
    date = models.DateField()
    observation = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.type} - {self.animal.name} - {self.date}"
