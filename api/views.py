from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view
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
from .utils import generate_invoice_pdf
import json
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import  *
from .serializers import *
from django.contrib.auth import get_user_model

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


class PaymeCallbackView(generics.GenericAPIView):
    serializer_class = PaymentCallbackSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction_id = serializer.validated_data['transaction_id']
        status = serializer.validated_data['status']

        try:
            payment = Payment.objects.get(transaction_id=transaction_id, payment_method='payme')
            payment.status = status
            payment.save()
            return Response({"message": "Payme payment status updated."}, status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

class ClickCallbackView(generics.GenericAPIView):
    serializer_class = PaymentCallbackSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction_id = serializer.validated_data['transaction_id']
        status = serializer.validated_data['status']

        try:
            payment = Payment.objects.get(transaction_id=transaction_id, payment_method='click')
            payment.status = status
            payment.save()
            return Response({"message": "Click payment status updated."}, status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)



class StripeCallbackView(generics.GenericAPIView):
    serializer_class = PaymentCallbackSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction_id = serializer.validated_data['transaction_id']
        status = serializer.validated_data['status']

        try:
            payment = Payment.objects.get(transaction_id=transaction_id, payment_method='stripe')
            payment.status = status
            payment.save()
            return Response({"message": "Stripe payment status updated."}, status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

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




























