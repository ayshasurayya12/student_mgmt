from django.db import models
from django.contrib.auth.models import User


class Principal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='principal_pics/', blank=True, null=True)

    def __str__(self):
        return f"Principal: {self.user.username}"