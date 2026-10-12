from django.db import models
from django.utils import timezone

# Create your models here.

class Photo(models.Model):
    who_id = models.IntegerField()
    image = models.ImageField(upload_to='photos/')
    created_at = models.DateTimeField(default=timezone.now)
