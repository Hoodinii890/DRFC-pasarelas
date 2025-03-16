import mercadopago
import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Payment
from django.db import transaction


class PaymentView(APIView):
    def post(self, request):
        print(request.data)
        if request.data.get('platform') == 'MP':
            # Recibir datos del frontend
            amount = request.data.get('amount')
            payment_method_id = request.data.get('payment_method_id')
            payer_email = request.data.get('payer_email')
            token = request.data.get('token')  # Este token debe ser generado de manera segura
            currency = request.data.get('currency')
            # Configurar Mercado Pago
            sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

            # Crear el pago
            payment_data = {
                "transaction_amount": amount,
                "payment_method_id": payment_method_id,
                "token": token,  # Aquí es donde se utiliza el token generado
                "description": "Prueba de pago",
                "installments": 1,
                "payer": {
                    "email": payer_email,
                    "entity_type": "individual",
                    "type": "customer",
                    "identification": {
                        "type": "CC",  # Tipo de identificación
                        "number": "123456789"  # Número de identificación
                    }
                },
                "additional_info": {
                    "items": [
                        {
                            "id": "YOUR_PRODUCT_ID",
                            "title": "Nombre del producto",
                            "description": "Descripción del producto",
                            "picture_url": "URL de la imagen del producto",
                            "category_id": "electronics",
                            "quantity": 1,
                            "unit_price": amount
                        }
                    ]
                }
            }

            # Realizar la solicitud a la API de Mercado Pago
            payment_response = sdk.payment().create(payment_data)

            if payment_response['status'] == 201:
                # Registrar el pago en el modelo
                Payment.objects.create(
                    amount=amount,
                    currency=currency,
                    status=payment_response['response']['status'],  # Obtener el estado del pago
                    transaction_amount=payment_response['response']['transaction_amount'],
                    payment_method_id=payment_response['response']['payment_method_id'],
                    payment_type_id=payment_response['response']['payment_type_id'],
                    description=payment_response['response']['description'],
                    payer_email=payer_email,
                    installments=payment_response['response']['installments'],
                    card_first_six_digits=payment_response['response']['card']['first_six_digits'],
                    card_last_four_digits=payment_response['response']['card']['last_four_digits'],
                    authorization_code=payment_response['response']['authorization_code'],
                    transaction_details=payment_response['response']['transaction_details'],
                    additional_info=payment_response['response']['additional_info'],
                    fees=payment_response['response']['fee_details'],  # Si hay detalles de tarifas
                    notification_url=payment_response['response'].get('notification_url', None),
                    platform = 'MP'
                )
                return Response(payment_response['response'], status=status.HTTP_201_CREATED)
            else:
                return Response(payment_response['response'], status=status.HTTP_400_BAD_REQUEST)
        elif request.data.get('platform') == 'Stripe':
            try:
                # Configurar Stripe con tu llave secreta
                stripe.api_key = settings.STRIPE_SECRET_KEY

                # Obtener datos del request
                amount = int(float(request.data.get('amount')) * 100)  # Stripe usa centavos
                currency = request.data.get('currency', 'usd')
                payment_method_id = request.data.get('payment_method_id')
                email = request.data.get('email')

                # Crear el pago
                payment_intent = stripe.PaymentIntent.create(
                    amount=amount,
                    currency=currency,
                    payment_method=payment_method_id,
                    confirmation_method='manual',
                    confirm=True,
                    return_url='https://tu-sitio.com/success',
                    receipt_email=email
                )

                # Si el pago es exitoso, guardar en tu modelo Payment
                if payment_intent.status in ['succeeded', 'requires_capture']:
                    # Obtener los detalles del método de pago
                    payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
                    
                    # Obtener el cargo si existe
                    charge = None
                    if payment_intent.latest_charge:
                        charge = stripe.Charge.retrieve(payment_intent.latest_charge)
                    
                    # Crear el pago en la base de datos
                    payment = Payment.objects.create(
                        amount=float(amount) / 100,
                        currency=currency,
                        status=payment_intent.status,
                        transaction_amount=float(amount) / 100,
                        payment_method_id=payment_method_id,
                        payment_type_id='card',
                        description='Pago con Stripe',
                        payer_email=email,
                        installments=1,
                        card_first_six_digits='',  # Stripe no proporciona los primeros 6 dígitos
                        card_last_four_digits=payment_method.card.last4 if hasattr(payment_method.card, 'last4') else None,
                        authorization_code=payment_intent.id,
                        transaction_details={
                            'id': payment_intent.id,
                            'status': payment_intent.status,
                            'payment_method': payment_method.id,
                            'card_type': payment_method.card.brand if hasattr(payment_method.card, 'brand') else None,
                            'charge_id': payment_intent.latest_charge if payment_intent.latest_charge else None
                        },
                        additional_info={
                            'receipt_url': charge.receipt_url if charge else None,
                            'card_brand': payment_method.card.brand if hasattr(payment_method.card, 'brand') else None,
                            'exp_month': payment_method.card.exp_month if hasattr(payment_method.card, 'exp_month') else None,
                            'exp_year': payment_method.card.exp_year if hasattr(payment_method.card, 'exp_year') else None,
                            'country': payment_method.card.country if hasattr(payment_method.card, 'country') else None,
                            'funding': payment_method.card.funding if hasattr(payment_method.card, 'funding') else None,
                            'charge_status': charge.status if charge else None,
                            'paid': charge.paid if charge else None
                        },
                        fees=None,
                        platform = 'Stripe'
                    )

                    return Response({
                        'status': 'success',
                        'payment_intent': payment_intent.id,
                        'client_secret': payment_intent.client_secret,
                        'charge_id': payment_intent.latest_charge if payment_intent.latest_charge else None
                    }, status=status.HTTP_201_CREATED)

                return Response({
                    'status': 'failed',
                    'error': 'Payment failed',
                    'payment_intent_status': payment_intent.status
                }, status=status.HTTP_400_BAD_REQUEST)

            except stripe.error.CardError as e:
                return Response({
                    'error': 'Card error',
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

            except stripe.error.StripeError as e:
                return Response({
                    'error': 'Stripe error',
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                return Response({
                    'error': 'Unknown error',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Si no se especifica una plataforma válida
        return Response({
            'error': 'Invalid platform',
            'message': 'Platform must be either MP or Stripe'
        }, status=status.HTTP_400_BAD_REQUEST)

class PaymentListView(APIView):
    def get_mercadoPago_payment(self, id, search_params=None):
        try:
            # Configurar Mercado Pago
            sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
            
            if id:
                # Buscar un pago específico
                payment_response = sdk.payment().get(id)
            else:
                # Construir los parámetros de búsqueda para Mercado Pago
                filters = {
                    "limit": 100,  # Número máximo de resultados
                    "offset": 0,
                    "sort": "date_created",
                    "criteria": "desc"
                }

                if search_params:
                    # Filtro por fecha
                    if search_params.get('created_after'):
                        filters["begin_date"] = "FROM " + search_params['created_after']
                    if search_params.get('created_before'):
                        filters["end_date"] = "TO " + search_params['created_before']

                    # Filtro por estado
                    if search_params.get('status'):
                        filters["status"] = search_params['status']

                    # Filtro por email
                    if search_params.get('customer_email'):
                        filters["payer.email"] = search_params['customer_email']

                    # Filtro por monto
                    if search_params.get('amount'):
                        filters["transaction_amount"] = float(search_params['amount'])

                # Realizar la búsqueda con los filtros
                payment_response = sdk.payment().search(filters)

            if payment_response['status'] == 200:
                # Formatear la respuesta para que sea similar a la de Stripe
                if id:
                    return payment_response['response']
                else:
                    formatted_payments = []
                    for payment in payment_response['response']['results']:
                        formatted_payment = {
                            'id': payment['id'],
                            'amount': float(payment['transaction_amount']),
                            'currency': payment['currency_id'],
                            'status': payment['status'],
                            'created': payment['date_created'],
                            'customer_email': payment['payer']['email'],
                            'payment_method': payment['payment_method_id'],
                            'description': payment['description'],
                            'metadata': payment.get('metadata', {}),
                            'card_details': {
                                'last_four_digits': payment.get('card', {}).get('last_four_digits'),
                                'first_six_digits': payment.get('card', {}).get('first_six_digits'),
                                'card_type': payment.get('payment_method_id'),
                            },
                            'transaction_details': payment.get('transaction_details', {}),
                            'fee_details': payment.get('fee_details', [])
                        }
                        formatted_payments.append(formatted_payment)
                    return formatted_payments
            else:
                return False

        except Exception as e:
            print(f"Error in MercadoPago payment search: {str(e)}")
            return False
        
    def get_stripe_payments(self, id,  search_params=None):
        # Si hay un ID específico
        if id:
            try:
                payment_intent = stripe.PaymentIntent.retrieve(
                    id,
                    expand=['customer', 'charges.data']
                )
                return payment_intent
            except stripe.error.StripeError as e:
                return False
        """
        Método para obtener pagos de Stripe con diferentes filtros
        """
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Parámetros base para la búsqueda
            params = {
                'limit': 100,  # Número máximo de resultados
                'expand': ['data.customer', 'data.charges.data']  # Incluir datos relacionados
            }

            # Agregar filtros si existen
            if search_params:
                if 'created_after' in search_params:
                    params['created[gte]'] = search_params['created_after']
                
                if 'created_before' in search_params:
                    params['created[lte]'] = search_params['created_before']
                
                if 'status' in search_params:
                    params['status'] = search_params['status']
                
                if 'customer_email' in search_params:
                    params['customer'] = stripe.Customer.list(
                        email=search_params['customer_email']
                    ).data[0].id if stripe.Customer.list(email=search_params['customer_email']).data else None

                if 'amount' in search_params:
                    # Stripe trabaja con centavos
                    params['amount'] = int(float(search_params['amount']) * 100)

            # Realizar la búsqueda
            payment_intents = stripe.PaymentIntent.list(**params)

            # Formatear los resultados
            formatted_payments = []
            for payment in payment_intents.data:
                formatted_payment = {
                    'id': payment.id,
                    'amount': float(payment.amount) / 100,  # Convertir de centavos
                    'currency': payment.currency,
                    'status': payment.status,
                    'created': payment.created,
                    'customer_email': payment.receipt_email,
                    'payment_method': payment.payment_method,
                    'description': payment.description,
                    'metadata': payment.metadata,
                }
                
                # Agregar información del cargo si existe
                if payment.latest_charge:
                    charge = stripe.Charge.retrieve(payment.latest_charge)
                    formatted_payment.update({
                        'receipt_url': charge.receipt_url,
                        'payment_method_details': charge.payment_method_details,
                        'paid': charge.paid,
                        'refunded': charge.refunded
                    })

                formatted_payments.append(formatted_payment)

            return formatted_payments

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")

    def get(self, request, *args, **kwargs):

        # Hacer la solicitud a la API de Mercado Pago para obtener los pagos
        try:
            # Obtener parámetros de búsqueda
            search_params = {
                'created_after': request.query_params.get('created_after'),
                'created_before': request.query_params.get('created_before'),
                'status': request.query_params.get('status'),
                'customer_email': request.query_params.get('email'),
                'amount': request.query_params.get('amount')
            }
            search_params = {k: v for k, v in search_params.items() if v is not None}
             # Verificar si se proporciona un ID para buscar un pago específico
            payment_id = kwargs.get('id')
            # Obtener pagos con los filtros aplicados
            MP_payments = self.get_mercadoPago_payment(id=payment_id, search_params=search_params)
            stripe_payments = self.get_stripe_payments(id=payment_id, search_params=search_params)

            if not any([stripe_payments, MP_payments]):
                if not MP_payments and not stripe_payments:
                    return Response({"error": "No payments found."}, status=status.HTTP_404_NOT_FOUND)
                
                return Response([pl for pl in [{"platform": "Stripe", "data":stripe_payments},{"platform":"MercadoPago","data":MP_payments}] if pl["data"] != False], status=status.HTTP_200_OK)
            return Response([pl for pl in [{"platform": "Stripe", "data":stripe_payments},{"platform":"MercadoPago","data":MP_payments}] if pl["data"] != False], status=status.HTTP_200_OK)


        except Exception as e:
            import traceback; traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)