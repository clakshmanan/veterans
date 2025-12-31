#!/usr/bin/env python
"""
Test script to verify state access permissions are working correctly.
Run this after applying the fixes to ensure the 403 error is resolved.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veteran_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory, Client
from django.urls import reverse
from veteran_app.models import State, UserState

def test_state_access():
    """Test state access functionality"""
    print("Testing state access permissions...")
    
    # Create test client
    client = Client()
    
    # Test 1: Check if states exist
    states = State.objects.all()
    print(f"Found {states.count()} states in database")
    
    if states.count() == 0:
        print("ERROR: No states found in database. Please add states first.")
        return False
    
    # Test 2: Check for state admin users
    state_users = UserState.objects.filter(approved=True)
    print(f"Found {state_users.count()} approved state admin users")
    
    if state_users.count() == 0:
        print("WARNING: No approved state admin users found.")
        return True
    
    # Test 3: Try to access state members page for each state
    for state in states[:3]:  # Test first 3 states
        url = reverse('state_members', kwargs={'state_id': state.id})
        print(f"Testing access to {url} for state: {state.name}")
        
        # Test without login (should redirect to login)
        response = client.get(url)
        if response.status_code == 302:
            print(f"  ✓ Unauthenticated access properly redirected (302)")
        else:
            print(f"  ✗ Unexpected status code for unauthenticated access: {response.status_code}")
        
        # Test with state admin user if available
        state_user = state_users.filter(state=state).first()
        if state_user:
            client.force_login(state_user.user)
            response = client.get(url)
            if response.status_code == 200:
                print(f"  ✓ State admin access successful (200)")
            else:
                print(f"  ✗ State admin access failed with status: {response.status_code}")
                if response.status_code == 403:
                    print(f"    ERROR: 403 Forbidden - The fix may not be working correctly!")
            client.logout()
    
    print("State access test completed.")
    return True

def check_permissions():
    """Check if users have necessary permissions"""
    print("\nChecking user permissions...")
    
    state_users = UserState.objects.filter(approved=True)
    
    for user_state in state_users[:5]:  # Check first 5 users
        user = user_state.user
        print(f"User: {user.username} (State: {user_state.state.name})")
        
        # Check if user has veteran member permissions
        perms = [
            'veteran_app.view_veteranmember',
            'veteran_app.add_veteranmember',
            'veteran_app.change_veteranmember'
        ]
        
        for perm in perms:
            has_perm = user.has_perm(perm)
            status = "✓" if has_perm else "✗"
            print(f"  {status} {perm}: {has_perm}")
    
    print("Permission check completed.")

if __name__ == '__main__':
    print("=" * 60)
    print("VETERAN APP - STATE ACCESS TEST")
    print("=" * 60)
    
    try:
        test_state_access()
        check_permissions()
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY:")
        print("- If you see 403 errors above, the fix needs more work")
        print("- If you see 200 status codes, the fix is working")
        print("- Run 'python manage.py fix_state_permissions' to assign permissions")
        print("=" * 60)
        
    except Exception as e:
        print(f"ERROR during testing: {e}")
        import traceback
        traceback.print_exc()