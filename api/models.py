from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = {
        'customuser': 'CustomUser',
        'accountant': 'Accountant',
    }
    phone_number = models.CharField(max_length=15, unique=True)
    username = models.CharField(max_length=30, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="customuser")
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']


    def __str__(self):
        return self.username


class AboutAccountant(models.Model):
    accountant = models.ForeignKey(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100)
    experience = models.IntegerField()
    education = models.TextField()
    certifications = models.TextField(blank=True, null=True)
    skills = models.TextField()
    languages = models.TextField()
    bio = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.accountant.username





class Video(models.Model):
    title = models.CharField(max_length=100)
    video = models.FileField(upload_to='video/', null=False, blank=False)

    def __str__(self):
        return self.title


class Xizmatlar(models.Model):
    title = models.CharField(max_length=100)
    img = models.ImageField(upload_to='xizmatlar/', null=False, blank=False)
    text = models.TextField(null=False, blank=False)

    def __str__(self):
        return self.title




class Narxlar(models.Model):
    name = models.CharField(max_length=100)
    offer = models.CharField(max_length=70)
    offer_two = models.CharField(max_length=70)
    offer_three = models.CharField(max_length=70)
    offer_four = models.CharField(max_length=70)
    price = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class AboutUs(models.Model):
    name = models.CharField(max_length=100)
    img = models.ImageField(upload_to='about/', null=False, blank=False)
    text = models.TextField(null=False, blank=False)

    def __str__(self):
        return self.name


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('canceled', 'Canceled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    client_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='UZS')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()

    def __str__(self):
        return f"Invoice {self.id} - {self.client_name}"



class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    ]

    PAYMENT_METHODS = [
        ('payme', 'Payme'),
        ('click', 'Click'),
        ('paypal', 'PayPal'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='UZS')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} - {self.amount} {self.currency} ({self.status})"


class TaxRate(models.Model):
    name = models.CharField(max_length=255)
    rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Tax rate in percentage")

    def __str__(self):
        return f"{self.name} ({self.rate}%)"







































































































