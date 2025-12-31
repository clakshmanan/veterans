# Association Number Verification Views

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import VeteranMember, AssociationVerification
import json

def verify_association_number(request, association_number):
    """Public verification endpoint for association numbers"""
    try:
        veteran = VeteranMember.objects.get(
            association_number=association_number,
            approved=True
        )
        
        # Check if ID card is still valid
        is_valid = veteran.is_id_card_valid()
        
        verification_data = {
            'valid': True,
            'association_number': veteran.association_number,
            'name': veteran.name,
            'rank': veteran.rank.name,
            'state': veteran.state.name,
            'id_card_valid': is_valid,
            'renewal_due': veteran.get_renewal_due_date().strftime('%Y-%m-%d') if veteran.get_renewal_due_date() else None,
            'association_date': veteran.association_date.strftime('%Y-%m-%d') if veteran.association_date else None
        }
        
        # Log verification attempt
        AssociationVerification.objects.create(
            association_number=association_number,
            verification_method='online',
            notes=f'Online verification from IP: {request.META.get("REMOTE_ADDR", "Unknown")}'
        )
        
        return JsonResponse(verification_data)
        
    except VeteranMember.DoesNotExist:
        return JsonResponse({
            'valid': False,
            'error': 'Association number not found or member not approved'
        }, status=404)

def verification_page(request, association_number=None):
    """Public verification page"""
    veteran = None
    if association_number:
        try:
            veteran = VeteranMember.objects.get(
                association_number=association_number,
                approved=True
            )
        except VeteranMember.DoesNotExist:
            pass
    
    return render(request, 'veteran_app/verify_association.html', {
        'veteran': veteran,
        'association_number': association_number
    })

@csrf_exempt
def bulk_verify_association(request):
    """Bulk verification endpoint for organizations"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        association_numbers = data.get('association_numbers', [])
        verifier_org = data.get('organization', 'Unknown')
        
        if not association_numbers or len(association_numbers) > 50:
            return JsonResponse({'error': 'Invalid request - max 50 numbers allowed'}, status=400)
        
        results = []
        for assoc_num in association_numbers:
            try:
                veteran = VeteranMember.objects.get(
                    association_number=assoc_num,
                    approved=True
                )
                
                results.append({
                    'association_number': assoc_num,
                    'valid': True,
                    'name': veteran.name,
                    'rank': veteran.rank.name,
                    'state': veteran.state.name,
                    'id_card_valid': veteran.is_id_card_valid()
                })
                
                # Log verification
                AssociationVerification.objects.create(
                    association_number=assoc_num,
                    verified_by=verifier_org,
                    verification_method='manual',
                    notes=f'Bulk verification by {verifier_org}'
                )
                
            except VeteranMember.DoesNotExist:
                results.append({
                    'association_number': assoc_num,
                    'valid': False,
                    'error': 'Not found'
                })
        
        return JsonResponse({'results': results})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)