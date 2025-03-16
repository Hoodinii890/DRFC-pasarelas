from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('amount', 'currency', 'status', 'created_at', 'payer_email')
    search_fields = ('payer_email', 'status')
    list_filter = ('status', 'currency')
