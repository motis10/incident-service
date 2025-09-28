#!/usr/bin/env python3
"""
Production mode request/response testing for Netanya Incident Service.
Tests the main API endpoints in production mode using mock SharePoint.
"""
import requests
import json
import base64
import time
import sys
import os
from typing import Dict, Any

def create_test_file() -> str:
    """Create a test base64 encoded image file."""
    # Create a small test PNG image (1x1 pixel)
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    return base64.b64encode(png_data).decode('utf-8')

def test_production_incident_submission(base_url: str = "http://localhost:8000") -> None:
    """Test incident submission in production mode."""
    print("🎯 PRODUCTION MODE - REQUEST/RESPONSE TESTING")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Basic Incident Submission (No File)",
            "data": {
                "user_data": {
                    "first_name": "דוד",
                    "last_name": "הפקה",
                    "phone": "0501234567",
                    "email": "david.production@netanya.muni.il"
                },
                "category": {
                    "id": 1,
                    "name": "תאורה",
                    "text": "Street lighting issues",
                    "image_url": "https://example.com/lighting.jpg",
                    "event_call_desc": "פנס רחוב לא עובד"
                },
                "street": {
                    "id": 123,
                    "name": "הרצל",
                    "image_url": "https://example.com/street.jpg",
                    "house_number": "25"
                },
                "custom_text": "🔧 בדיקת מצב פרודקשן - בעיית תאורה רחוב"
            }
        },
        {
            "name": "Incident with File Attachment",
            "data": {
                "user_data": {
                    "first_name": "מרים",
                    "last_name": "פרודקשן",
                    "phone": "0507654321",
                    "email": "miriam.prod@netanya.muni.il"
                },
                "category": {
                    "id": 2,
                    "name": "ניקיון",
                    "text": "Cleaning issues",
                    "image_url": "https://example.com/cleaning.jpg",
                    "event_call_desc": "זבל ברחוב"
                },
                "street": {
                    "id": 456,
                    "name": "ויצמן",
                    "image_url": "https://example.com/weizmann.jpg",
                    "house_number": "50"
                },
                "custom_text": "📸 יש תמונה המוכיחה את הבעיה",
                "extra_files": [
                    {
                        "filename": "evidence.png",
                        "content_type": "image/png",
                        "file_data": create_test_file()
                    }
                ]
            }
        },
        {
            "name": "Long Description Test",
            "data": {
                "user_data": {
                    "first_name": "אבי",
                    "last_name": "טסטר",
                    "phone": "0501112233",
                    "email": "avi.tester@netanya.muni.il"
                },
                "category": {
                    "id": 3,
                    "name": "כבישים",
                    "text": "Road maintenance",
                    "image_url": "https://example.com/roads.jpg",
                    "event_call_desc": "בעיה בכביש"
                },
                "street": {
                    "id": 789,
                    "name": "בן גוריון",
                    "image_url": "https://example.com/bengurion.jpg",
                    "house_number": "100"
                },
                "custom_text": "🛣️ בדיקת טקסט ארוך מאוד: יש בעיה חמורה בכביש הראשי של העיר, עם בורות גדולים שגורמים נזק לרכבים. הבעיה קיימת כבר מספר חודשים ודורשת טיפול דחוף. תושבים רבים התלוננו על הנושא ואף נגרם נזק לרכבים. בנוסף, הבעיה מהווה סכנה בטיחותית משמעותית לנוסעים ולהולכי הרגל באזור. דרושה פעולה מיידית לתיקון הכביש והחזרת הבטיחות לאזור."
            }
        }
    ]
    
    print(f"\n🌐 Testing against: {base_url}")
    print(f"📅 Test time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test service health first
    print(f"\n0️⃣ Pre-flight Health Check...")
    try:
        health_response = requests.get(f"{base_url}/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   ✅ Service Status: {health_data.get('status')}")
            print(f"   🔧 Debug Mode: {health_data.get('debug_mode')}")
            print(f"   🌍 Environment: {health_data.get('environment', 'unknown')}")
        else:
            print(f"   ❌ Health check failed: {health_response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return
    
    # Run incident submission tests
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ {test_case['name']}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            # Make the request
            response = requests.post(
                f"{base_url}/incidents/submit",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            # Display results
            print(f"   📊 Status Code: {response.status_code}")
            print(f"   ⏱️  Response Time: {response_time:.2f}ms")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS")
                ticket_id = response_data.get('ticket_id', 'N/A')
                correlation_id = response_data.get('correlation_id', 'N/A')
                print(f"   🎫 Ticket ID: {ticket_id}")
                print(f"   🔍 Correlation ID: {correlation_id}")
                
                # Check for file processing info
                if 'file_info' in response_data:
                    file_info = response_data['file_info']
                    print(f"   📎 File: {file_info.get('filename')} ({file_info.get('size_mb')}MB)")
                
                results.append({"test": test_case['name'], "status": "PASS", "time": response_time})
                
            elif response.status_code == 422:
                print("   ⚠️  VALIDATION ERROR")
                errors = response_data.get('field_errors', [])
                for error in errors[:3]:  # Show first 3 errors
                    print(f"      • {error.get('field', 'unknown')}: {error.get('message', 'validation error')}")
                results.append({"test": test_case['name'], "status": "VALIDATION_ERROR", "time": response_time})
                
            elif response.status_code >= 500:
                print("   ❌ SERVER ERROR")
                error_msg = response_data.get('error', response_data.get('details', 'Unknown error'))
                correlation_id = response_data.get('correlation_id', 'N/A')
                print(f"      Error: {error_msg}")
                print(f"      Correlation ID: {correlation_id}")
                results.append({"test": test_case['name'], "status": "SERVER_ERROR", "time": response_time})
                
            else:
                print(f"   ❓ UNEXPECTED STATUS: {response.status_code}")
                print(f"      Response: {str(response_data)[:200]}...")
                results.append({"test": test_case['name'], "status": "UNEXPECTED", "time": response_time})
            
            # Show response headers of interest
            interesting_headers = ['x-correlation-id', 'x-request-id', 'content-type']
            for header in interesting_headers:
                if header in response.headers:
                    print(f"   📋 {header}: {response.headers[header]}")
                    
        except requests.exceptions.Timeout:
            print("   ⏰ REQUEST TIMEOUT")
            results.append({"test": test_case['name'], "status": "TIMEOUT", "time": 30000})
            
        except requests.exceptions.ConnectionError:
            print("   🔌 CONNECTION ERROR")
            results.append({"test": test_case['name'], "status": "CONNECTION_ERROR", "time": 0})
            
        except Exception as e:
            print(f"   💥 UNEXPECTED ERROR: {e}")
            results.append({"test": test_case['name'], "status": "ERROR", "time": 0})
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PRODUCTION TESTING SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r['status'] in ['PASS'])
    total = len(results)
    avg_time = sum(r['time'] for r in results if r['time'] > 0) / max(1, len([r for r in results if r['time'] > 0]))
    
    for result in results:
        status_emoji = {
            'PASS': '✅',
            'VALIDATION_ERROR': '⚠️',
            'SERVER_ERROR': '❌',
            'TIMEOUT': '⏰',
            'CONNECTION_ERROR': '🔌',
            'ERROR': '💥',
            'UNEXPECTED': '❓'
        }.get(result['status'], '❓')
        
        print(f"   {status_emoji} {result['test']}: {result['status']} ({result['time']:.0f}ms)")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    print(f"⏱️  Average response time: {avg_time:.2f}ms")
    
    if passed == total:
        print("🎉 ALL PRODUCTION TESTS PASSED!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - CHECK LOGS")
        return False

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    success = test_production_incident_submission(base_url)
    sys.exit(0 if success else 1)
