from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = {
        'customuser': 'CustomUser',
        'accountant': 'Accountant',
        'admin': 'Admin',
    }
    phone_number = models.CharField(max_length=15, unique=True)
    username = models.CharField(max_length=30, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="customuser")
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name','email', 'phone_number','role']


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


class Experience(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    currently_working = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValueError("End date must be after start date")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} at {self.company}"



class ReferenceRequest(models.Model):
    sender = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    recipient = models.EmailField()
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)

class Reference(models.Model):
    request = models.OneToOneField(ReferenceRequest, on_delete=models.CASCADE)
    feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)



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





class ChatRoom(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    participants = models.ManyToManyField(User, related_name="chat_rooms")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Chat {self.id}"

class Message(models.Model):
    chat = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to="chat_files/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.text[:20] if self.text else 'File uploaded'}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.message[:20]}"




class Request(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="requests")
    accountant = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="accepted_requests")
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()

    company_name = models.CharField(max_length=255)
    company_key = models.CharField(max_length=50, unique=True)
    company_type = models.CharField(max_length=50, choices=[('LLC', 'MChJ'), ('SP', 'XK'), ('JSC', 'AJ')])
    company_activity = models.CharField(max_length=255)
    legal_address = models.TextField()

    bank_account = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    bank_mfo = models.CharField(max_length=10, blank=True, null=True)
    tax_system = models.CharField(max_length=50, choices=[('general', 'Umumiy'), ('simplified', 'Soddalashtirilgan')])
    is_vat_payer = models.BooleanField(default=False)

    service_type = models.CharField(max_length=255)
    document_count = models.PositiveIntegerField()
    order_deadline = models.DateField()

    additional_files = models.FileField(upload_to='orders/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} - {self.service_type} ({self.status})"


class Card(models.Model):
    CARDS = (
        ('6262570125113045', '6262570125113045'),
        ('3654263263263267', '3654263263263267'),
    )

    STATUS_CHOICES = (
        ('boshlandi', 'Boshlandi'),
        ('tekshirilmoqda', 'Tekshirilmoqda'),
        ('tugatildi', 'Tugatildi'),
    )

    card = models.CharField(max_length=16, choices=CARDS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='boshlandi')

    def __str__(self):
        return f"Card {self.card} - {self.status}"





















































































