from django.urls import path
from .views import PaymentView, PaymentListView

urlpatterns = [
    path('payments/', PaymentView.as_view(), name='payment'),  # Ruta para procesar pagos
    path('payments/list/<str:id>', PaymentListView.as_view(), name='payment-list-id'),  # Ruta para obtener los pagos
    path('payments/list/', PaymentListView.as_view(), name='payment-list'),  # Ruta para obtener los pagos
]
