from django.db import models
from django.core.validators import RegexValidator

# Create your models here.

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^(\+[0-9]{1,3})?[0-9]{10}$|^[0-9]{3}-[0-9]{3}-[0-9]{4}$',
                message="Phone number must be in the format: '+1234567890' or '123-456-7890'",
            ),
        ],
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
