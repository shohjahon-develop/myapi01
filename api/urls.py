from django.urls import path, include
from rest_framework.routers import DefaultRouter


from .views import *

router = DefaultRouter()
router.register(r'xizmatlar', XizmatlarViewSet)
router.register(r'narxlar', NarxlarViewSet)
router.register(r'about',AboutViewSet)
router.register(r'aboutAccountant',AboutAccountantViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),

    path('videos/', get_videos, name='get_videos'),

    path('', include(router.urls)),

    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),


    path('invoices/', InvoiceListCreateView.as_view(), name='invoice_list_create'),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/export/pdf/', InvoicePDFExportView.as_view(), name='invoice_export_pdf'),

    
    path('payments/', PaymentListCreateView.as_view(), name='payment_list_create'),
    path('payments/<int:pk>/status/', PaymentStatusUpdateView.as_view(), name='payment_status_update'),
    path('payments/start/', PaymentStartView.as_view(), name='payment_start'),
    path('payments/callback/payme/', PaymeCallbackView.as_view(), name='payme_callback'),
    path('payments/callback/click/', ClickCallbackView.as_view(), name='click_callback'),
    path('payments/callback/stripe/', StripeCallbackView.as_view(), name='stripe_callback'),
    path('payments/callback/paypal/', PayPalCallbackView.as_view(), name='paypal_callback'),
    path('payments/<int:pk>/status/', PaymentStatusView.as_view(), name='payment_status'),

    path('taxes/calculate/', TaxCalculationView.as_view(), name='tax_calculation'),
    path('taxes/reports/', TaxReportView.as_view(), name='tax_report'),
    path('user/balance/', UserBalanceView.as_view(), name='user_balance'),
    path('user/financial-report/', FinancialReportView.as_view(), name='financial_report'),
    path('user/financial-report/export/pdf/', FinancialReportPDFView.as_view(), name='financial_report_pdf'),
    path('user/financial-report/export/excel/', FinancialReportExcelView.as_view(), name='financial_report_excel'),


]
