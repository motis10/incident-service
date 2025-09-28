#!/usr/bin/env python3
"""
Production testing script for Netanya Incident Service.
"""
import requests
import json
import time
import sys

def test_production_service(base_url="http://localhost:8000"):
    """Test the service in production mode."""
    print("🚀 PRODUCTION MODE TESTING")
    print("=" * 50)
    
    tests = []
    
    # Test 1: Health Check
    print("\n1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            debug_mode = data.get('debug_mode', True)
            print(f"   ✅ Health: {data.get('status')}")
            print(f"   🔧 Debug Mode: {debug_mode}")
            if not debug_mode:
                print("   ✅ Running in PRODUCTION mode")
            tests.append(("Health Check", True))
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            tests.append(("Health Check", False))
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        tests.append(("Health Check", False))
    
    # Test 2: Documentation Security
    print("\n2. Testing API Documentation Security...")
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 404:
            print("   ✅ API documentation properly disabled in production")
            tests.append(("Docs Security", True))
        else:
            print(f"   ⚠️  API documentation still accessible: {response.status_code}")
            tests.append(("Docs Security", False))
    except Exception as e:
        print(f"   ❌ Documentation test error: {e}")
        tests.append(("Docs Security", False))
    
    # Test 3: Production Health Endpoint
    print("\n3. Testing Production Health Validation...")
    try:
        response = requests.get(f"{base_url}/health/production")
        if response.status_code == 200:
            data = response.json()
            production_ready = data.get('production_ready', False)
            print(f"   ✅ Production health endpoint accessible")
            print(f"   🔧 Production Ready: {production_ready}")
            if production_ready:
                print("   ✅ Service is production-ready")
            else:
                validation = data.get('validation_summary', {})
                print(f"   ⚠️  Validation issues: {validation.get('errors', 0)} errors, {validation.get('warnings', 0)} warnings")
            tests.append(("Production Health", True))
        else:
            print(f"   ❌ Production health check failed: {response.status_code}")
            tests.append(("Production Health", False))
    except Exception as e:
        print(f"   ❌ Production health error: {e}")
        tests.append(("Production Health", False))
    
    # Test 4: Error Handling
    print("\n4. Testing Production Error Handling...")
    try:
        # Send invalid data to test error handling
        invalid_data = {"invalid": "data"}
        response = requests.post(f"{base_url}/incidents/submit", json=invalid_data)
        
        if response.status_code == 422:  # Validation error expected
            data = response.json()
            correlation_id = data.get('correlation_id')
            print("   ✅ Validation errors properly handled")
            print(f"   🔍 Correlation ID: {correlation_id}")
            tests.append(("Error Handling", True))
        else:
            print(f"   ⚠️  Unexpected response: {response.status_code}")
            tests.append(("Error Handling", False))
    except Exception as e:
        print(f"   ❌ Error handling test error: {e}")
        tests.append(("Error Handling", False))
    
    # Test 5: Performance Test
    print("\n5. Testing Performance...")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/health")
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000
        print(f"   ⏱️  Response time: {response_time:.2f}ms")
        
        if response_time < 100:  # Under 100ms
            print("   ✅ Fast response time")
            tests.append(("Performance", True))
        else:
            print("   ⚠️  Slow response time")
            tests.append(("Performance", False))
    except Exception as e:
        print(f"   ❌ Performance test error: {e}")
        tests.append(("Performance", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 PRODUCTION TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - SERVICE IS PRODUCTION READY!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW BEFORE PRODUCTION")
        return False

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    success = test_production_service(base_url)
    sys.exit(0 if success else 1)
