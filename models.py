from drfc.models import CoreModel
from django.db import models

methods = [('MP', 'Mercado Pago'), ('Stripe', 'Stripe')]

class Payment(CoreModel):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    payment_method_id = models.CharField(max_length=50, null=True)
    payment_type_id = models.CharField(max_length=50, null=True)
    description = models.TextField(null=True)
    payer_email = models.EmailField(null=True)
    installments = models.IntegerField(null=True)
    card_first_six_digits = models.CharField(max_length=6, null=True)
    card_last_four_digits = models.CharField(max_length=4, null=True)
    authorization_code = models.CharField(max_length=50, null=True)
    transaction_details = models.JSONField(null=True)  # Para almacenar detalles de la transacción
    additional_info = models.JSONField(null=True)  # Para almacenar información adicional
    fees = models.JSONField(null=True)  # Para almacenar detalles de tarifas
    notification_url = models.URLField(null=True)
    platform = models.CharField(max_length=20, choices=methods, null=True)

    def __str__(self):
        return f"{self.amount} {self.currency} - {self.status}"