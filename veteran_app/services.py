import razorpay
import uuid
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import PaymentGateway, PaymentOrder, EventRegistration

class PaymentService:
    """Service class for handling payments"""
    
    def __init__(self):
        self.gateway = PaymentGateway.objects.filter(name='razorpay', is_active=True).first()
        if self.gateway:
            self.client = razorpay.Client(auth=(self.gateway.api_key, self.gateway.secret_key))
    
    def create_order(self, veteran, order_type, amount, description, event_registration=None):
        """Create payment order"""
        if not self.gateway:
            raise Exception("No active payment gateway found")
        
        # Generate unique order ID
        order_id = f"ORD_{uuid.uuid4().hex[:8].upper()}"
        
        # Create Razorpay order
        razorpay_order = self.client.order.create({
            'amount': int(amount * 100),  # Amount in paise
            'currency': 'INR',
            'receipt': order_id,
            'payment_capture': 1
        })
        
        # Create local order record
        payment_order = PaymentOrder.objects.create(
            order_id=order_id,
            veteran=veteran,
            order_type=order_type,
            amount=amount,
            description=description,
            gateway=self.gateway,
            gateway_order_id=razorpay_order['id'],
            event_registration=event_registration
        )
        
        return payment_order, razorpay_order
    
    def verify_payment(self, payment_id, order_id, signature):
        """Verify payment signature"""
        try:
            self.client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
            return True
        except:
            return False
    
    def process_successful_payment(self, payment_order, payment_id):
        """Process successful payment"""
        payment_order.status = 'completed'
        payment_order.gateway_payment_id = payment_id
        payment_order.paid_at = timezone.now()
        payment_order.save()
        
        # Update related objects
        if payment_order.event_registration:
            registration = payment_order.event_registration
            registration.payment_status = 'completed'
            registration.payment_id = payment_id
            registration.status = 'confirmed'
            registration.save()
        
        return payment_order