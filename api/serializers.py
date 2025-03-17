from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.serializers import Serializer, EmailField, CharField, ModelSerializer, DecimalField
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from api.models import *
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_number','role']



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username','first_name', 'last_name','email','phone_number', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True)

class JWTSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['client', 'status', 'created_at', 'updated_at']

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['title', 'video']

class AboutAccountantSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutAccountant
        fields = '__all__'


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = '__all__'



class XizmatlarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Xizmatlar
        fields = '__all__'


class NarxlarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Narxlar
        fields = '__all__'

class AboutUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutUs
        fields = '__all__'



class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bunday email bilan foydalanuvchi topilmadi!")
        return value

    def send_reset_email(self):
        email = self.validated_data["email"]
        user = User.objects.get(email=email)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = f"http://yourfrontend.com/password-reset/{uid}/{token}/"

        send_mail(
            subject="Parolni tiklash",
            message=f"Parolingizni tiklash uchun quyidagi linkdan foydalaning: {reset_url}",
            from_email="mrzaqulovbegzod@gmail.com",
            recipient_list=[email],
            fail_silently=False,
        )


class PasswordResetSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        try:
            uid = force_str(urlsafe_base64_decode(data["uid"]))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError):
            raise serializers.ValidationError("Noto‘g‘ri yoki eskirgan link!")

        if not default_token_generator.check_token(user, data["token"]):
            raise serializers.ValidationError("Token noto‘g‘ri yoki eskirgan!")

        return {"user": user, "new_password": data["new_password"]}

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save()


class InvoiceSerializer(ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'


class PaymentSerializer(ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class PaymentStatusUpdateSerializer(Serializer):
    status = CharField()


class PaymentStartSerializer(Serializer):
    invoice_id = CharField()
    payment_method = CharField()


class PaymentCallbackSerializer(Serializer):
    transaction_id = CharField()
    status = CharField()


class TaxCalculationSerializer(Serializer):
    amount = DecimalField(max_digits=10, decimal_places=2)
    tax_rate_id = CharField()


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = '__all__'
        read_only_fields = ['user']

    def validate(self, data):
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError("End date must be after start date")
        return data


class ReferenceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferenceRequest
        fields = '__all__'

class ReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reference
        fields = '__all__'



class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = "__all__"

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField()
    file = serializers.FileField(required=False)

    class Meta:
        model = Message
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"



class RequestSerializer(serializers.ModelSerializer):
    client = serializers.StringRelatedField(read_only=True)
    accountant = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Request
        fields = "__all__"
        read_only_fields = ["client", "status"]
























