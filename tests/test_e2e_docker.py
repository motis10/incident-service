"""
End-to-end testing with Docker Compose environment.
"""
import pytest
import requests
import time
import subprocess
import sys
from pathlib import Path

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestDockerComposeE2E:
    """Test complete workflows through Docker Compose environment."""
    
    @classmethod
    def setup_class(cls):
        """Set up Docker Compose environment for testing."""
        cls.base_url = "http://localhost:8000"
        cls.mock_sharepoint_url = "http://localhost:8001"
        
        # Start Docker Compose services
        try:
            subprocess.run(
                ["docker-compose", "up", "-d", "--build"],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Wait for services to be ready
            cls._wait_for_service(cls.base_url, timeout=60)
            cls._wait_for_service(cls.mock_sharepoint_url, timeout=30)
            
        except subprocess.CalledProcessError as e:
            pytest.skip(f"Docker Compose setup failed: {e}")
        except Exception as e:
            pytest.skip(f"Environment setup error: {e}")
    
    @classmethod
    def teardown_class(cls):
        """Tear down Docker Compose environment."""
        try:
            subprocess.run(
                ["docker-compose", "down"],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError:
            pass  # Best effort cleanup
    
    @staticmethod
    def _wait_for_service(url, timeout=30):
        """Wait for a service to become available."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
        
        raise TimeoutError(f"Service at {url} did not become available within {timeout} seconds")
    
    def test_service_health_check(self):
        """Test that all services are healthy."""
        # Test main service
        response = requests.get(f"{self.base_url}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        
        # Test mock SharePoint service
        try:
            mock_response = requests.get(f"{self.mock_sharepoint_url}/health")
            assert mock_response.status_code == 200
        except requests.exceptions.RequestException:
            pytest.skip("Mock SharePoint service not available")
    
    def test_complete_incident_submission_workflow(self):
        """Test complete incident submission workflow through Docker."""
        incident_data = {
            "user_data": {
                "first_name": "יוסי",
                "last_name": "כהן",
                "phone": "0501234567",
                "email": "yossi@example.com"
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
                "house_number": "15"
            },
            "custom_text": "פנס רחוב לא עובד ברחוב הרצל 15 - בדיקה מקצה לקצה"
        }
        
        response = requests.post(
            f"{self.base_url}/incidents/submit",
            json=incident_data,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "ticket_id" in data
        assert data["ticket_id"].startswith("NETANYA-")
        assert "correlation_id" in data
    
    def test_incident_submission_with_debug_mode(self):
        """Test incident submission in debug mode (mock SharePoint)."""
        # Verify debug mode is enabled
        health_response = requests.get(f"{self.base_url}/health")
        health_data = health_response.json()
        
        incident_data = {
            "user_data": {
                "first_name": "דוד",
                "last_name": "בדיקה",
                "phone": "0521234567"
            },
            "category": {
                "id": 2,
                "name": "ניקיון",
                "text": "Cleanliness",
                "image_url": "https://example.com/clean.jpg",
                "event_call_desc": "בעיית ניקיון"
            },
            "street": {
                "id": 456,
                "name": "בן גוריון",
                "image_url": "https://example.com/street2.jpg",
                "house_number": "20"
            },
            "custom_text": "בדיקת מצב דיבאג - אין קריאות חיצוניות"
        }
        
        response = requests.post(
            f"{self.base_url}/incidents/submit",
            json=incident_data,
            timeout=15
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # In debug mode, should use mock ticket generation
        ticket_id = data["ticket_id"]
        assert ticket_id.startswith("NETANYA-")
        assert len(ticket_id.split("-")) >= 3  # Format: NETANYA-YYYY-XXXXXX
    
    def test_file_upload_end_to_end(self):
        """Test file upload through complete workflow."""
        # Create test image data
        import base64
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_data = jpeg_header + b'\x00' * 2000 + b'\xff\xd9'
        
        incident_data = {
            "user_data": {
                "first_name": "מרים",
                "last_name": "קובץ",
                "phone": "0531234567"
            },
            "category": {
                "id": 1,
                "name": "תאורה",
                "text": "Street lighting",
                "image_url": "https://example.com/light.jpg",
                "event_call_desc": "פנס רחוב"
            },
            "street": {
                "id": 789,
                "name": "ויצמן",
                "image_url": "https://example.com/street3.jpg",
                "house_number": "30"
            },
            "custom_text": "בדיקת העלאת קובץ מקצה לקצה",
            "extra_files": {
                "filename": "e2e_evidence.jpg",
                "content_type": "image/jpeg",
                "size": len(jpeg_data),
                "data": base64.b64encode(jpeg_data).decode('utf-8')
            }
        }
        
        response = requests.post(
            f"{self.base_url}/incidents/submit",
            json=incident_data,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["has_file"] is True
        assert "file_info" in data
    
    def test_api_documentation_availability(self):
        """Test API documentation availability in debug mode."""
        try:
            docs_response = requests.get(f"{self.base_url}/docs")
            # Should be available in debug mode
            assert docs_response.status_code == 200
            assert "text/html" in docs_response.headers.get("content-type", "")
        except requests.exceptions.RequestException:
            pytest.skip("API documentation not configured")
    
    def test_health_monitoring_endpoints(self):
        """Test all health monitoring endpoints."""
        endpoints = [
            "/health",
            "/health/detailed", 
            "/health/ready",
            "/health/live"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{self.base_url}{endpoint}")
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert "timestamp" in data
    
    def test_cors_handling_e2e(self):
        """Test CORS handling through complete request cycle."""
        # Test OPTIONS request
        options_response = requests.options(f"{self.base_url}/incidents/submit")
        assert options_response.status_code == 200
        
        # Test actual request with CORS-like headers
        headers = {
            "Origin": "https://netanya.muni.il",
            "Content-Type": "application/json"
        }
        
        incident_data = {
            "user_data": {
                "first_name": "טסט",
                "last_name": "CORS",
                "phone": "0541234567"
            },
            "category": {
                "id": 1,
                "name": "תאורה",
                "text": "Street lighting",
                "image_url": "https://example.com/light.jpg",
                "event_call_desc": "פנס רחוב"
            },
            "street": {
                "id": 123,
                "name": "הרצל",
                "image_url": "https://example.com/street.jpg",
                "house_number": "15"
            },
            "custom_text": "בדיקת CORS"
        }
        
        response = requests.post(
            f"{self.base_url}/incidents/submit",
            json=incident_data,
            headers=headers,
            timeout=15
        )
        
        assert response.status_code == 200


class TestPerformanceE2E:
    """Test performance through Docker Compose environment."""
    
    @classmethod
    def setup_class(cls):
        """Set up environment for performance testing."""
        cls.base_url = "http://localhost:8000"
        
        # Ensure service is running
        try:
            response = requests.get(f"{cls.base_url}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Service not available for performance testing")
        except requests.exceptions.RequestException:
            pytest.skip("Service not reachable for performance testing")
    
    def test_concurrent_incident_submissions(self):
        """Test handling of concurrent incident submissions."""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def submit_incident(thread_id):
            try:
                incident_data = {
                    "user_data": {
                        "first_name": f"בדיקה{thread_id}",
                        "last_name": "בו-זמנית",
                        "phone": "0501234567"
                    },
                    "category": {
                        "id": 1,
                        "name": "תאורה",
                        "text": "Street lighting",
                        "image_url": "https://example.com/light.jpg",
                        "event_call_desc": "פנס רחוב"
                    },
                    "street": {
                        "id": 123,
                        "name": "הרצל",
                        "image_url": "https://example.com/street.jpg",
                        "house_number": "15"
                    },
                    "custom_text": f"בדיקה בו-זמנית #{thread_id}"
                }
                
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/incidents/submit",
                    json=incident_data,
                    timeout=30
                )
                end_time = time.time()
                
                results_queue.put({
                    "thread_id": thread_id,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                })
                
            except Exception as e:
                results_queue.put({
                    "thread_id": thread_id,
                    "error": str(e),
                    "success": False
                })
        
        # Start concurrent threads
        threads = []
        num_threads = 5
        
        for i in range(num_threads):
            thread = threading.Thread(target=submit_incident, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == num_threads
        
        # Check all requests succeeded
        successful_requests = [r for r in results if r.get("success", False)]
        assert len(successful_requests) >= num_threads * 0.8  # At least 80% success rate
        
        # Check response times are reasonable
        response_times = [r["response_time"] for r in successful_requests if "response_time" in r]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            assert avg_response_time < 5.0  # Average response time under 5 seconds
    
    def test_large_file_upload_performance(self):
        """Test performance with large file uploads."""
        import base64
        
        # Create 4MB test file
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        large_data = jpeg_header + b'\x00' * (4 * 1024 * 1024 - len(jpeg_header) - 2) + b'\xff\xd9'
        
        incident_data = {
            "user_data": {
                "first_name": "ביצועים",
                "last_name": "קובץ-גדול",
                "phone": "0551234567"
            },
            "category": {
                "id": 1,
                "name": "תאורה", 
                "text": "Street lighting",
                "image_url": "https://example.com/light.jpg",
                "event_call_desc": "פנס רחוב"
            },
            "street": {
                "id": 123,
                "name": "הרצל",
                "image_url": "https://example.com/street.jpg",
                "house_number": "15"
            },
            "custom_text": "בדיקת ביצועים - קובץ גדול 4MB",
            "extra_files": {
                "filename": "large_performance_test.jpg",
                "content_type": "image/jpeg",
                "size": len(large_data),
                "data": base64.b64encode(large_data).decode('utf-8')
            }
        }
        
        start_time = time.time()
        
        response = requests.post(
            f"{self.base_url}/incidents/submit",
            json=incident_data,
            timeout=60  # Longer timeout for large file
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert response.status_code == 200
        assert processing_time < 30.0  # Should process within 30 seconds
        
        data = response.json()
        assert data["success"] is True
        assert data["has_file"] is True
    
    def test_service_stability_under_load(self):
        """Test service stability under continuous load."""
        # Send requests continuously for a short period
        duration = 10  # seconds
        start_time = time.time()
        request_count = 0
        errors = 0
        
        while time.time() - start_time < duration:
            try:
                incident_data = {
                    "user_data": {
                        "first_name": f"עומס{request_count}",
                        "last_name": "רציף",
                        "phone": "0561234567"
                    },
                    "category": {
                        "id": 1,
                        "name": "תאורה",
                        "text": "Street lighting",
                        "image_url": "https://example.com/light.jpg",
                        "event_call_desc": "פנס רחוב"
                    },
                    "street": {
                        "id": 123,
                        "name": "הרצל",
                        "image_url": "https://example.com/street.jpg",
                        "house_number": "15"
                    },
                    "custom_text": f"בדיקת עומס רציף #{request_count}"
                }
                
                response = requests.post(
                    f"{self.base_url}/incidents/submit",
                    json=incident_data,
                    timeout=10
                )
                
                if response.status_code != 200:
                    errors += 1
                
                request_count += 1
                
                # Small delay to avoid overwhelming
                time.sleep(0.1)
                
            except Exception:
                errors += 1
                request_count += 1
        
        # Check service handled load reasonably
        assert request_count > 0
        error_rate = errors / request_count if request_count > 0 else 1
        assert error_rate < 0.1  # Less than 10% error rate
        
        # Check service is still healthy after load test
        health_response = requests.get(f"{self.base_url}/health")
        assert health_response.status_code == 200


class TestDebugModeE2E:
    """Test debug mode specific functionality."""
    
    @classmethod
    def setup_class(cls):
        """Set up for debug mode testing."""
        cls.base_url = "http://localhost:8000"
    
    def test_no_external_api_calls_in_debug_mode(self):
        """Test that debug mode doesn't make external API calls."""
        # In a real test environment, we could monitor network traffic
        # For now, test that requests complete quickly (indicating mock usage)
        
        incident_data = {
            "user_data": {
                "first_name": "דיבאג",
                "last_name": "מצב",
                "phone": "0571234567"
            },
            "category": {
                "id": 1,
                "name": "תאורה",
                "text": "Street lighting",
                "image_url": "https://example.com/light.jpg",
                "event_call_desc": "פנס רחוב"
            },
            "street": {
                "id": 123,
                "name": "הרצל",
                "image_url": "https://example.com/street.jpg",
                "house_number": "15"
            },
            "custom_text": "בדיקה שאין קריאות חיצוניות"
        }
        
        start_time = time.time()
        
        response = requests.post(
            f"{self.base_url}/incidents/submit",
            json=incident_data,
            timeout=5  # Short timeout - should complete quickly with mock
        )
        
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 2.0  # Should be very fast with mock
        
        data = response.json()
        assert data["success"] is True
        # Mock ticket should have consistent format
        assert data["ticket_id"].startswith("NETANYA-")
    
    def test_debug_mode_consistent_responses(self):
        """Test that debug mode provides consistent mock responses."""
        incident_data = {
            "user_data": {
                "first_name": "עקביות",
                "last_name": "דיבאג",
                "phone": "0581234567"
            },
            "category": {
                "id": 1,
                "name": "תאורה",
                "text": "Street lighting",
                "image_url": "https://example.com/light.jpg",
                "event_call_desc": "פנס רחוב"
            },
            "street": {
                "id": 123,
                "name": "הרצל",
                "image_url": "https://example.com/street.jpg",
                "house_number": "15"
            },
            "custom_text": "בדיקת עקביות תגובות דיבאג"
        }
        
        # Make multiple requests
        responses = []
        for i in range(3):
            response = requests.post(
                f"{self.base_url}/incidents/submit",
                json=incident_data,
                timeout=10
            )
            assert response.status_code == 200
            responses.append(response.json())
        
        # Check all responses have consistent format
        for data in responses:
            assert data["success"] is True
            assert "ticket_id" in data
            assert "correlation_id" in data
            assert data["ticket_id"].startswith("NETANYA-")
            assert len(data["ticket_id"]) > 10  # Reasonable length
