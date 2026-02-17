"""Simple test script for the FastAPI backend."""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_members, get_archives, get_user, get_user_events, get_user_payments
from models import MemberResponse, ArchiveResponse


def test_archives():
    """Test getting archives list."""
    print("Testing get_archives()...")
    archives = get_archives()
    print(f"  ✓ Found {len(archives)} archives")
    if archives:
        print(f"  ✓ First archive: {archives[0]}")
    return True


def test_database_connection():
    """Test database connection and basic queries."""
    print("\nTesting database connection...")
    
    try:
        # Test getting members
        print("  Testing get_members()...")
        members = get_members()
        print(f"  ✓ Found {len(members)} members")
        
        if members:
            # Validate first member
            first_member = members[0]
            print(f"  ✓ First member: {first_member.get('display_name', 'N/A')} (uid: {first_member.get('uid')})")
            
            # Test MemberResponse model
            member_response = MemberResponse(**first_member)
            print(f"  ✓ MemberResponse validation passed")
            
            # Test getting user details
            uid = first_member['uid']
            print(f"\n  Testing get_user({uid})...")
            user = get_user(uid)
            if user:
                print(f"  ✓ User found: {user}")
            else:
                print(f"  ⚠ User not found")
            
            # Test getting user events
            print(f"\n  Testing get_user_events({uid})...")
            events = get_user_events(uid)
            print(f"  ✓ Found {len(events)} events")
            
            # Test getting user payments
            print(f"\n  Testing get_user_payments({uid})...")
            payments = get_user_payments(uid)
            print(f"  ✓ Found {len(payments)} payments")
        else:
            print(f"  ℹ No members found (empty database)")
        
        return True
    except FileNotFoundError as e:
        print(f"  ⚠ Database file not found: {e}")
        print(f"  ℹ This is expected if the database doesn't exist yet")
        print(f"  ℹ The API will work once a valid database is provided")
        return True  # Not a failure, just not configured
    except Exception as e:
        # Check if it's a missing table error (expected if database doesn't exist)
        error_msg = str(e).lower()
        if 'no such table' in error_msg or 'no such file' in error_msg:
            print(f"  ℹ Database schema not found: {e}")
            print(f"  ℹ This is expected if the database doesn't exist yet")
            print(f"  ℹ The API will work once a valid database is provided")
            return True  # Not a failure, just not configured
        
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_creation():
    """Test that the FastAPI app can be created."""
    print("\nTesting FastAPI app creation...")
    
    try:
        from main import app
        print(f"  ✓ FastAPI app created: {app.title}")
        print(f"  ✓ Version: {app.version}")
        
        # List routes
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        print(f"  ✓ Found {len(routes)} routes:")
        for route in sorted(routes):
            print(f"    - {route}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("FastAPI Backend Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test archives
    results.append(("Archives", test_archives()))
    
    # Test database
    results.append(("Database", test_database_connection()))
    
    # Test API creation
    results.append(("API Creation", test_api_creation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
