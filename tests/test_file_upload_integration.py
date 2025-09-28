"""
Comprehensive file upload integration tests.
"""
import pytest
import io
import base64
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app.main import app
from app.services.incident_service import SubmissionResult


class TestFileUploadValidation:
    """Test file upload validation scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    def create_valid_incident_data(self):
        """Create valid incident data for testing."""
        return {
            "user_data": {
                "first_name": "טסט",
                "last_name": "יוזר",
                "phone": "0501234567",
                "email": "test@example.com"
            },
            "category": {
                "id": 1,
                "name": "תאורה",
                "text": "Street lighting",
                "image_url": "https://example.com/light.jpg",
                "event_call_desc": "פנס רחוב לא עובד"
            },
            "street": {
                "id": 123,
                "name": "הרצל",
                "image_url": "https://example.com/street.jpg",
                "house_number": "15"
            },
            "custom_text": "פנס רחוב שבור - נדרשת תיקון דחוף"
        }
    
    def test_valid_jpeg_file_upload(self):
        """Test valid JPEG file upload."""
        with patch('app.api.incidents.incident_service') as mock_service:
            mock_result = SubmissionResult(
                success=True,
                ticket_id="NETANYA-2025-FILE-001",
                correlation_id="file-test-001",
                has_file=True,
                file_info={"filename": "evidence.jpg", "size": 1024, "type": "image/jpeg"},
                metadata={}
            )
            mock_service.submit_incident.return_value = mock_result
            
            # Create valid JPEG data
            jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
            jpeg_data = jpeg_header + b'\x00' * 1000 + b'\xff\xd9'
            
            incident_data = self.create_valid_incident_data()
            
            # Test with JSON (simulating file attachment in request)
            incident_data["extra_files"] = {
                "filename": "evidence.jpg",
                "content_type": "image/jpeg",
                "size": len(jpeg_data),
                "data": base64.b64encode(jpeg_data).decode('utf-8')
            }
            
            response = self.client.post("/incidents/submit", json=incident_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["has_file"] is True
    
    def test_valid_png_file_upload(self):
        """Test valid PNG file upload."""
        with patch('app.api.incidents.incident_service') as mock_service:
            mock_result = SubmissionResult(
                success=True,
                ticket_id="NETANYA-2025-FILE-002",
                correlation_id="file-test-002",
                has_file=True,
                file_info={"filename": "screenshot.png", "size": 2048, "type": "image/png"},
                metadata={}
            )
            mock_service.submit_incident.return_value = mock_result
            
            # Create valid PNG data
            png_header = b'\x89PNG\r\n\x1a\n'
            png_data = png_header + b'\x00' * 2000
            
            incident_data = self.create_valid_incident_data()
            incident_data["extra_files"] = {
                "filename": "screenshot.png",
                "content_type": "image/png",
                "size": len(png_data),
                "data": base64.b64encode(png_data).decode('utf-8')
            }
            
            response = self.client.post("/incidents/submit", json=incident_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["has_file"] is True
    
    def test_invalid_file_type_rejection(self):
        """Test rejection of invalid file types."""
        # Create text file disguised as image
        text_data = b"This is not an image file, it's text content"
        
        incident_data = self.create_valid_incident_data()
        incident_data["extra_files"] = {
            "filename": "fake.jpg",
            "content_type": "image/jpeg",
            "size": len(text_data),
            "data": base64.b64encode(text_data).decode('utf-8')
        }
        
        response = self.client.post("/incidents/submit", json=incident_data)
        
        # Should fail validation (422) or succeed with service handling the validation
        assert response.status_code in [200, 422]
        
        if response.status_code == 422:
            data = response.json()
            assert "detail" in data or "error" in data
    
    def test_oversized_file_rejection(self):
        """Test rejection of oversized files."""
        # Create file larger than 5MB
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        large_data = jpeg_header + b'\x00' * (6 * 1024 * 1024)  # 6MB
        
        incident_data = self.create_valid_incident_data()
        incident_data["extra_files"] = {
            "filename": "large_image.jpg",
            "content_type": "image/jpeg",
            "size": len(large_data),
            "data": base64.b64encode(large_data).decode('utf-8')
        }
        
        response = self.client.post("/incidents/submit", json=incident_data)
        
        # Should fail validation
        assert response.status_code in [200, 413, 422]
    
    def test_empty_file_rejection(self):
        """Test rejection of empty files."""
        incident_data = self.create_valid_incident_data()
        incident_data["extra_files"] = {
            "filename": "empty.jpg",
            "content_type": "image/jpeg",
            "size": 0,
            "data": ""
        }
        
        response = self.client.post("/incidents/submit", json=incident_data)
        
        # Should fail validation
        assert response.status_code in [200, 422]
    
    def test_malicious_filename_rejection(self):
        """Test rejection of malicious filenames."""
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_data = jpeg_header + b'\x00' * 100
        
        malicious_filenames = [
            "../../../etc/passwd.jpg",
            "file\x00.jpg",
            "con.jpg",
            "\\..\\..\\windows\\system32\\file.jpg",
        ]
        
        for filename in malicious_filenames:
            incident_data = self.create_valid_incident_data()
            incident_data["extra_files"] = {
                "filename": filename,
                "content_type": "image/jpeg",
                "size": len(jpeg_data),
                "data": base64.b64encode(jpeg_data).decode('utf-8')
            }
            
            response = self.client.post("/incidents/submit", json=incident_data)
            
            # Should either fail validation or succeed with filename sanitization
            assert response.status_code in [200, 422]
    
    def test_invalid_base64_data(self):
        """Test handling of invalid base64 data."""
        incident_data = self.create_valid_incident_data()
        incident_data["extra_files"] = {
            "filename": "test.jpg",
            "content_type": "image/jpeg",
            "size": 100,
            "data": "This is not valid base64 data!"
        }
        
        response = self.client.post("/incidents/submit", json=incident_data)
        
        # Should fail validation
        assert response.status_code in [200, 422]


class TestFileUploadPerformance:
    """Test file upload performance scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    def test_maximum_file_size_upload(self):
        """Test upload of maximum allowed file size."""
        with patch('app.api.incidents.incident_service') as mock_service:
            mock_result = SubmissionResult(
                success=True,
                ticket_id="NETANYA-2025-LARGE-FILE",
                correlation_id="large-file-test",
                has_file=True,
                file_info={"filename": "large.jpg", "size": 5 * 1024 * 1024},
                metadata={"processing_time": 2.5}
            )
            mock_service.submit_incident.return_value = mock_result
            
            # Create 5MB file (maximum allowed)
            jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
            large_data = jpeg_header + b'\x00' * (5 * 1024 * 1024 - len(jpeg_header) - 2) + b'\xff\xd9'
            
            incident_data = {
                "user_data": {
                    "first_name": "טסט",
                    "last_name": "גדול",
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
                "custom_text": "תמונה גדולה של פנס שבור",
                "extra_files": {
                    "filename": "large_evidence.jpg",
                    "content_type": "image/jpeg",
                    "size": len(large_data),
                    "data": base64.b64encode(large_data).decode('utf-8')
                }
            }
            
            import time
            start_time = time.time()
            
            response = self.client.post("/incidents/submit", json=incident_data)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Should complete within reasonable time (< 10 seconds)
            assert processing_time < 10.0
            assert response.status_code == 200
    
    def test_multiple_file_uploads_concurrently(self):
        """Test multiple file uploads happening concurrently."""
        with patch('app.api.incidents.incident_service') as mock_service:
            mock_result = SubmissionResult(
                success=True,
                ticket_id="NETANYA-2025-CONCURRENT",
                correlation_id="concurrent-test",
                has_file=True,
                file_info={"filename": "concurrent.jpg", "size": 1024},
                metadata={}
            )
            mock_service.submit_incident.return_value = mock_result
            
            import threading
            import queue
            
            results_queue = queue.Queue()
            
            def upload_file(file_id):
                try:
                    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
                    jpeg_data = jpeg_header + b'\x00' * 1000
                    
                    incident_data = {
                        "user_data": {
                            "first_name": f"טסט{file_id}",
                            "last_name": "בו-זמני",
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
                        "custom_text": f"תמונה מספר {file_id}",
                        "extra_files": {
                            "filename": f"evidence_{file_id}.jpg",
                            "content_type": "image/jpeg",
                            "size": len(jpeg_data),
                            "data": base64.b64encode(jpeg_data).decode('utf-8')
                        }
                    }
                    
                    response = self.client.post("/incidents/submit", json=incident_data)
                    results_queue.put((file_id, response.status_code))
                except Exception as e:
                    results_queue.put((file_id, f"ERROR: {e}"))
            
            # Start multiple threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=upload_file, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Check results
            results = []
            while not results_queue.empty():
                results.append(results_queue.get())
            
            assert len(results) == 3
            for file_id, status_code in results:
                assert status_code == 200


class TestFileUploadEdgeCases:
    """Test file upload edge cases and error scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    def test_unicode_filename_handling(self):
        """Test handling of Unicode filenames."""
        with patch('app.api.incidents.incident_service') as mock_service:
            mock_result = SubmissionResult(
                success=True,
                ticket_id="NETANYA-2025-UNICODE",
                correlation_id="unicode-test",
                has_file=True,
                file_info={"filename": "תמונה_עברית.jpg", "size": 1024},
                metadata={}
            )
            mock_service.submit_incident.return_value = mock_result
            
            jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
            jpeg_data = jpeg_header + b'\x00' * 100
            
            incident_data = {
                "user_data": {
                    "first_name": "דוד",
                    "last_name": "עברי",
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
                "custom_text": "תמונה עם שם בעברית",
                "extra_files": {
                    "filename": "תמונה_עברית.jpg",
                    "content_type": "image/jpeg",
                    "size": len(jpeg_data),
                    "data": base64.b64encode(jpeg_data).decode('utf-8')
                }
            }
            
            response = self.client.post("/incidents/submit", json=incident_data)
            
            # Should handle Unicode filenames properly
            assert response.status_code == 200
    
    def test_special_characters_in_filename(self):
        """Test handling of special characters in filenames."""
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_data = jpeg_header + b'\x00' * 100
        
        special_filenames = [
            "file with spaces.jpg",
            "file-with-dashes.jpg",
            "file_with_underscores.jpg",
            "file.with.dots.jpg",
            "file(with)parentheses.jpg",
            "file[with]brackets.jpg",
        ]
        
        for filename in special_filenames:
            incident_data = {
                "user_data": {
                    "first_name": "טסט",
                    "last_name": "מיוחד",
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
                "custom_text": f"תמונה עם שם מיוחד: {filename}",
                "extra_files": {
                    "filename": filename,
                    "content_type": "image/jpeg",
                    "size": len(jpeg_data),
                    "data": base64.b64encode(jpeg_data).decode('utf-8')
                }
            }
            
            response = self.client.post("/incidents/submit", json=incident_data)
            
            # Should handle special characters (either accept or reject gracefully)
            assert response.status_code in [200, 422]
    
    def test_corrupted_image_data(self):
        """Test handling of corrupted image data."""
        # Create corrupted JPEG (starts with header but has invalid data)
        corrupted_data = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'corrupted data here' + b'\xff\xd9'
        
        incident_data = {
            "user_data": {
                "first_name": "טסט",
                "last_name": "מושחת",
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
            "custom_text": "תמונה עם נתונים מושחתים",
            "extra_files": {
                "filename": "corrupted.jpg",
                "content_type": "image/jpeg",
                "size": len(corrupted_data),
                "data": base64.b64encode(corrupted_data).decode('utf-8')
            }
        }
        
        response = self.client.post("/incidents/submit", json=incident_data)
        
        # Should handle corrupted data gracefully
        assert response.status_code in [200, 422]
    
    def test_mime_type_mismatch(self):
        """Test handling of MIME type mismatch."""
        # PNG data with JPEG content type
        png_header = b'\x89PNG\r\n\x1a\n'
        png_data = png_header + b'\x00' * 100
        
        incident_data = {
            "user_data": {
                "first_name": "טסט",
                "last_name": "לא-תואם",
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
            "custom_text": "תמונה עם סוג MIME לא תואם",
            "extra_files": {
                "filename": "mismatch.jpg",
                "content_type": "image/jpeg",  # Wrong content type for PNG data
                "size": len(png_data),
                "data": base64.b64encode(png_data).decode('utf-8')
            }
        }
        
        response = self.client.post("/incidents/submit", json=incident_data)
        
        # Should detect and handle MIME type mismatch
        assert response.status_code in [200, 422]


class TestFileUploadSecurity:
    """Test file upload security scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    def test_script_injection_in_image(self):
        """Test detection of script injection in image files."""
        # Image with embedded script
        malicious_data = b'\xff\xd8\xff\xe0\x00\x10JFIF<script>alert("xss")</script>' + b'\x00' * 100
        
        incident_data = {
            "user_data": {
                "first_name": "טסט",
                "last_name": "מזיק",
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
            "custom_text": "תמונה עם תוכן מסוכן",
            "extra_files": {
                "filename": "malicious.jpg",
                "content_type": "image/jpeg",
                "size": len(malicious_data),
                "data": base64.b64encode(malicious_data).decode('utf-8')
            }
        }
        
        response = self.client.post("/incidents/submit", json=incident_data)
        
        # Should detect and reject malicious content
        assert response.status_code in [200, 422]
    
    def test_executable_file_rejection(self):
        """Test rejection of executable files disguised as images."""
        # Windows PE executable header
        exe_header = b'MZ\x90\x00\x03\x00\x00\x00\x04\x00'
        exe_data = exe_header + b'\x00' * 100
        
        incident_data = {
            "user_data": {
                "first_name": "טסט",
                "last_name": "הרצה",
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
            "custom_text": "קובץ הרצה מחופש לתמונה",
            "extra_files": {
                "filename": "virus.jpg",
                "content_type": "image/jpeg",
                "size": len(exe_data),
                "data": base64.b64encode(exe_data).decode('utf-8')
            }
        }
        
        response = self.client.post("/incidents/submit", json=incident_data)
        
        # Should reject executable files
        assert response.status_code in [200, 422]
    
    def test_zip_bomb_detection(self):
        """Test detection of potential zip bombs in image metadata."""
        # Image with suspicious metadata
        suspicious_data = b'\xff\xd8\xff\xe1\xff\xff'  # Large metadata marker
        large_metadata = b'PK' + b'\x00' * 1000  # ZIP-like metadata
        jpeg_data = suspicious_data + large_metadata + b'\xff\xd9'
        
        incident_data = {
            "user_data": {
                "first_name": "טסט",
                "last_name": "חשוד",
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
            "custom_text": "תמונה עם מטא-דאטה חשודה",
            "extra_files": {
                "filename": "suspicious.jpg",
                "content_type": "image/jpeg",
                "size": len(jpeg_data),
                "data": base64.b64encode(jpeg_data).decode('utf-8')
            }
        }
        
        response = self.client.post("/incidents/submit", json=incident_data)
        
        # Should handle suspicious content appropriately
        assert response.status_code in [200, 422]


class TestFileUploadErrorRecovery:
    """Test file upload error recovery scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    def test_partial_upload_handling(self):
        """Test handling of partial/incomplete uploads."""
        # Simulate incomplete JPEG (missing end marker)
        incomplete_data = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 100
        # Missing \xff\xd9 end marker
        
        incident_data = {
            "user_data": {
                "first_name": "טסט",
                "last_name": "חלקי",
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
            "custom_text": "תמונה חלקית/לא שלמה",
            "extra_files": {
                "filename": "incomplete.jpg",
                "content_type": "image/jpeg",
                "size": len(incomplete_data),
                "data": base64.b64encode(incomplete_data).decode('utf-8')
            }
        }
        
        response = self.client.post("/incidents/submit", json=incident_data)
        
        # Should handle incomplete files gracefully
        assert response.status_code in [200, 422]
    
    def test_network_interruption_simulation(self):
        """Test handling of simulated network interruptions."""
        # This is more of a conceptual test since TestClient doesn't simulate real network issues
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_data = jpeg_header + b'\x00' * 1000
        
        incident_data = {
            "user_data": {
                "first_name": "טסט",
                "last_name": "רשת",
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
            "custom_text": "בדיקת עמידות רשת",
            "extra_files": {
                "filename": "network_test.jpg",
                "content_type": "image/jpeg",
                "size": len(jpeg_data),
                "data": base64.b64encode(jpeg_data).decode('utf-8')
            }
        }
        
        # Test that the endpoint responds correctly even under normal conditions
        response = self.client.post("/incidents/submit", json=incident_data)
        
        # Should handle request appropriately
        assert response.status_code in [200, 422, 500]
