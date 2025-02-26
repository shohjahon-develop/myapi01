from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.serializers import Serializer, EmailField, CharField, ModelSerializer, DecimalField
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from api.models import *

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_number','role']



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username','first_name', 'last_name','phone_number', 'password']

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


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['title', 'video']

class AboutAccountantSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutAccountant
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


class PasswordResetRequestSerializer(Serializer):
    email = EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bunday email bilan user topilmadi!")
        return value


class PasswordResetSerializer(Serializer):
    uid = CharField()
    token = CharField()
    new_password = CharField(write_only=True, min_length=8)


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
























