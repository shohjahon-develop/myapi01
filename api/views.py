from requests.models import Request
from xml import parsers
from rest_framework.permissions import IsAdminUser
from django.contrib.admin import action
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view
from rest_framework import permissions

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.core.mail import send_mail

from myapi01.settings import PAYME_URL, PAYME_MERCHANT_ID, CLICK_URL, CLICK_MERCHANT_ID
from .utils import generate_invoice_pdf
import json
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import  *
from .serializers import *
from django.contrib.auth import get_user_model
import openpyxl

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(username=serializer.validated_data['username'],
                            password=serializer.validated_data['password'])
        if user:
            tokens = get_tokens_for_user(user)
            return Response(tokens, status=status.HTTP_200_OK)
        return Response({"error": "Username or password error!"}, status=status.HTTP_401_UNAUTHORIZED)

class UserProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user



@api_view(['GET'])
def get_videos(request):
    videos = Video.objects.all()
    serializer = VideoSerializer(videos, many=True) 
    return Response(serializer.data)

class AboutAccountantViewSet(viewsets.ModelViewSet):
    queryset = AboutAccountant.objects.all()
    serializer_class = AboutAccountantSerializer

class XizmatlarViewSet(viewsets.ModelViewSet):
    queryset = Xizmatlar.objects.all()
    serializer_class = XizmatlarSerializer


class NarxlarViewSet(viewsets.ModelViewSet):
    queryset = Narxlar.objects.all()
    serializer_class = NarxlarSerializer

class AboutViewSet(viewsets.ModelViewSet):
    queryset = AboutUs.objects.all()
    serializer_class = AboutUsSerializer


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(phone_number=serializer.validated_data['phone_number'])
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"http://Accounting.com/reset-password/{uid}/{token}/"

        send_mail(
            "Password Reset Request",
            f"Passwordingizni o'zgartirish uchun buyerga bosing: {reset_url}",
            "no-reply@yourdomain.com",
            [user.phone_number],
        )
        return Response({"message": "Password reset link sent."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            uid = urlsafe_base64_decode(serializer.validated_data['uid']).decode()
            user = User.objects.get(pk=uid)
            if default_token_generator.check_token(user, serializer.validated_data['token']):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Invalid request."}, status=status.HTTP_400_BAD_REQUEST)



class InvoiceListCreateView(generics.ListCreateAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class InvoiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)





class InvoicePDFExportView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        try:
            invoice = Invoice.objects.get(pk=pk, user=request.user)
            return generate_invoice_pdf(invoice)
        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)






class PaymentListCreateView(generics.ListCreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PaymentStatusUpdateView(generics.UpdateAPIView):
    serializer_class = PaymentStatusUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        payment = self.get_object()
        serializer = self.get_serializer(payment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        payment.status = serializer.validated_data['status']
        payment.save()
        return Response({"message": "Payment status updated successfully."}, status=status.HTTP_200_OK)


class PaymentStartView(generics.GenericAPIView):
    serializer_class = PaymentStartSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invoice_id = serializer.validated_data['invoice_id']
        payment_method = serializer.validated_data['payment_method']

        try:
            invoice = Invoice.objects.get(id=invoice_id, user=request.user)
            payment = Payment.objects.create(
                user=request.user,
                invoice=invoice,
                amount=invoice.amount,
                currency=invoice.currency,
                payment_method=payment_method,
                status='pending'
            )
            return Response({"message": "Payment started.", "payment_id": payment.id}, status=status.HTTP_201_CREATED)
        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)


class PaymeCheckoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, invoice_id, *args, **kwargs):
        try:
            invoice = Invoice.objects.get(id=invoice_id, user=request.user)
            payme_link = f"{PAYME_URL}/?merchant={PAYME_MERCHANT_ID}&amount={int(invoice.amount * 100)}&account[invoice_id]={invoice.id}"
            return Response({"payme_link": payme_link}, status=status.HTTP_200_OK)
        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)

class ClickCheckoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, invoice_id, *args, **kwargs):
        try:
            invoice = Invoice.objects.get(id=invoice_id, user=request.user)
            click_link = f"{CLICK_URL}/?service_id={CLICK_MERCHANT_ID}&amount={invoice.amount}&transaction_param={invoice.id}"
            return Response({"click_link": click_link}, status=status.HTTP_200_OK)
        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)


class PayPalCallbackView(generics.GenericAPIView):
    serializer_class = PaymentCallbackSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction_id = serializer.validated_data['transaction_id']
        status = serializer.validated_data['status']

        try:
            payment = Payment.objects.get(transaction_id=transaction_id, payment_method='paypal')
            payment.status = status
            payment.save()
            return Response({"message": "PayPal payment status updated."}, status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)


class PaymentStatusView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        try:
            payment = Payment.objects.get(pk=pk, user=request.user)
            return Response({"payment_id": payment.id, "status": payment.status}, status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)


class TaxCalculationView(generics.GenericAPIView):
    serializer_class = TaxCalculationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data['amount']
        tax_rate_id = serializer.validated_data['tax_rate_id']

        try:
            tax_rate = TaxRate.objects.get(id=tax_rate_id)
            tax_amount = (amount * tax_rate.rate) / 100
            return Response({"amount": amount, "tax": tax_amount, "total": amount + tax_amount},
                            status=status.HTTP_200_OK)
        except TaxRate.DoesNotExist:
            return Response({"error": "Tax rate not found."}, status=status.HTTP_404_NOT_FOUND)


class TaxReportView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        invoices = Invoice.objects.filter(user=request.user, status='paid')
        total_income = sum(invoice.amount for invoice in invoices)
        tax_rates = TaxRate.objects.all()

        tax_data = []
        total_tax = 0
        for tax_rate in tax_rates:
            tax_amount = (total_income * tax_rate.rate) / 100
            total_tax += tax_amount
            tax_data.append({
                "tax_name": tax_rate.name,
                "tax_rate": tax_rate.rate,
                "tax_amount": tax_amount
            })

        return Response({
            "total_income": total_income,
            "total_tax": total_tax,
            "net_income": total_income - total_tax,
            "tax_breakdown": tax_data
        }, status=status.HTTP_200_OK)


class UserBalanceView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        invoices = Invoice.objects.filter(user=request.user, status='paid')
        total_income = sum(invoice.amount for invoice in invoices)

        payments = Payment.objects.filter(user=request.user, status='successful')
        total_expense = sum(payment.amount for payment in payments)

        tax_rates = TaxRate.objects.all()
        total_tax = sum((total_income * tax.rate) / 100 for tax in tax_rates)

        balance = total_income - total_expense - total_tax

        return Response({
            "total_income": total_income,
            "total_expense": total_expense,
            "total_tax": total_tax,
            "balance": balance
        }, status=status.HTTP_200_OK)


class FinancialReportView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        period = request.GET.get("period", "monthly")
        today = datetime.today()

        if period == "daily":
            start_date = today - timedelta(days=1)
        elif period == "weekly":
            start_date = today - timedelta(weeks=1)
        else:  # Default: monthly
            start_date = today - timedelta(days=30)

        invoices = Invoice.objects.filter(user=request.user, status='paid', created_at__gte=start_date)
        payments = Payment.objects.filter(user=request.user, status='successful', created_at__gte=start_date)

        total_income = sum(invoice.amount for invoice in invoices)
        total_expense = sum(payment.amount for payment in payments)
        balance = total_income - total_expense

        return Response({
            "period": period,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance
        }, status=status.HTTP_200_OK)


class FinancialReportPDFView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="financial_report.pdf"'

        p = canvas.Canvas(response, pagesize=letter)
        p.drawString(100, 750, "Financial Report")

        invoices = Invoice.objects.filter(user=request.user, status='paid')
        total_income = sum(invoice.amount for invoice in invoices)
        payments = Payment.objects.filter(user=request.user, status='successful')
        total_expense = sum(payment.amount for payment in payments)
        balance = total_income - total_expense

        p.drawString(100, 730, f"Total Income: {total_income} UZS")
        p.drawString(100, 710, f"Total Expense: {total_expense} UZS")
        p.drawString(100, 690, f"Balance: {balance} UZS")

        p.showPage()
        p.save()
        return response


# Financial Report Excel Export View
class FinancialReportExcelView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="financial_report.xlsx"'

        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Financial Report"
        sheet.append(["Total Income", "Total Expense", "Balance"])

        invoices = Invoice.objects.filter(user=request.user, status='paid')
        total_income = sum(invoice.amount for invoice in invoices)
        payments = Payment.objects.filter(user=request.user, status='successful')
        total_expense = sum(payment.amount for payment in payments)
        balance = total_income - total_expense

        sheet.append([total_income, total_expense, balance])

        workbook.save(response)
        return response


class ExperienceViewSet(viewsets.ModelViewSet):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Experience.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['GET'])
    def my_experiences(self, request):
        experiences = self.get_queryset()
        serializer = self.get_serializer(experiences, many=True)
        return Response(serializer.data)


class ReferenceRequestViewSet(viewsets.ModelViewSet):
    queryset = ReferenceRequest.objects.all()
    serializer_class = ReferenceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        reference_request = self.get_object()
        reference_request.is_accepted = True
        reference_request.save()
        return Response({'status': 'Reference request accepted'})


class ReferenceViewSet(viewsets.ModelViewSet):
    queryset = Reference.objects.all()
    serializer_class = ReferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        reference_request = ReferenceRequest.objects.get(id=self.request.data.get('request_id'))
        if reference_request.is_accepted:
            serializer.save(request=reference_request)
        else:
            return Response({'error': 'Request not accepted yet'}, status=400)



class ChatRoomViewSet(viewsets.ModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(participants=self.request.user)

    def perform_create(self, serializer):
        chat = serializer.save()
        chat.participants.add(self.request.user)  # Avtomatik yaratuvchini qo‘shish


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]  # Fayl yuklash uchun parser

    def get_queryset(self):
        chat_id = self.request.query_params.get("chat")
        if chat_id:
            return self.queryset.filter(chat_id=chat_id).order_by("-created_at")
        return self.queryset.none()

    def perform_create(self, serializer):
        chat_id = self.request.data.get("chat")
        chat = get_object_or_404(ChatRoom, id=chat_id, participants=self.request.user)
        serializer.save(sender=self.request.user, chat=chat)




class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"message": "Notification marked as read"})





class SystemStatisticsView(APIView):
    permission_classes = [IsAdminUser]  # Faqat adminlar ko‘ra oladi

    def get(self, request):
        total_users = User.objects.count()
        total_clients = User.objects.filter(is_staff=False).count()
        total_accountants = User.objects.filter(is_staff=True).count()

        total_requests = Request.objects.count()
        pending_requests = Request.objects.filter(status="pending").count()
        accepted_requests = Request.objects.filter(status="accepted").count()
        completed_requests = Request.objects.filter(status="completed").count()

        total_invoices = Invoice.objects.count()
        paid_invoices = Invoice.objects.filter(status="paid").count()
        unpaid_invoices = Invoice.objects.filter(status="pending").count()

        return Response({
            "users": {
                "total": total_users,
                "clients": total_clients,
                "accountants": total_accountants,
            },
            "requests": {
                "total": total_requests,
                "pending": pending_requests,
                "accepted": accepted_requests,
                "completed": completed_requests,
            },
            "invoices": {
                "total": total_invoices,
                "paid": paid_invoices,
                "unpaid": unpaid_invoices,
            }
        })


class RequestViewSet(viewsets.ModelViewSet):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset.filter(status='pending')  # Buxgalterlar faqat 'pending' so‘rovlarni ko‘radi
        return self.queryset.filter(client=self.request.user)  # Mijozlar faqat o‘z so‘rovlarini ko‘radi

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        request = get_object_or_404(Request, id=pk, status='pending')
        request.accountant = request.user
        request.status = 'accepted'
        request.save()
        return Response({"message": "So‘rov qabul qilindi", "status": request.status})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        request = get_object_or_404(Request, id=pk, status='accepted', accountant=request.user)
        request.status = 'completed'
        request.save()
        return Response({"message": "So‘rov bajarildi", "status": request.status})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        request = get_object_or_404(Request, id=pk, status='pending')
        request.status = 'rejected'
        request.save()
        return Response({"message": "So‘rov rad etildi", "status": request.status})











