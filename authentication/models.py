from django.db import models
from shop.models import User


class Key(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_index=True)
    data = models.CharField(max_length=512, unique=True)
    expire_time = models.DateTimeField()
