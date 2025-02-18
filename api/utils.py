# utils.py
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_invoice_pdf(invoice):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.id}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    p.drawString(100, 750, f"Invoice ID: {invoice.id}")
    p.drawString(100, 730, f"Client: {invoice.client_name}")
    p.drawString(100, 710, f"Email: {invoice.client_email}")
    p.drawString(100, 690, f"Amount: {invoice.amount} {invoice.currency}")
    p.drawString(100, 670, f"Status: {invoice.status}")
    p.drawString(100, 650, f"Due Date: {invoice.due_date}")
    p.showPage()
    p.save()
    return response
