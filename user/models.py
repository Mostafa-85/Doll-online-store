from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# Create your models here.

class UserProfile(models.Model):
    user= models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
    phone =models.CharField(max_length=11,
        validators=[RegexValidator(regex=r'^\d{11}$', message="شماره تلفن باید 11 رقم باشد.")],
        null=True,blank=True
    )
    address = models.TextField(null=True,blank=True)
    email_confirmation =models.BooleanField(default=False)
    # shopping_cart = 

    def __str__(self):
        return f"Profile of {self.user.username}"
    
