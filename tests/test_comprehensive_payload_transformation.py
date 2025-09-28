"""
Comprehensive tests for payload transformation with all field mappings.
"""
import pytest
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app.services.payload_transformation import PayloadTransformer, TransformationError
from app.models.request import IncidentSubmissionRequest, UserData, IncidentCategory
from app.models.sharepoint import APIPayload


class TestBasicPayloadTransformation:
    """Test basic payload transformation scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = PayloadTransformer()
    
    def test_basic_transformation(self):
        """Test basic incident request transformation."""
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="יוסי",
                last_name="כהן",
                phone="0501234567",
                email="yossi@example.com"
            ),
            category=IncidentCategory(
                name="תאורה",
                description="Street lighting issues"
            ),
            description="פנס רחוב לא עובד ברחוב הרצל 5",
            address="רחוב הרצל 5, נתניה"
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        
        # Verify fixed municipality values
        assert payload.eventCallSourceId == 4
        assert payload.cityCode == "7400"
        assert payload.cityDesc == "נתניה"
        assert payload.eventCallCenterId == "3"
        assert payload.contactUsType == "3"
        
        # Verify user data mapping
        assert payload.callerFirstName == "יוסי"
        assert payload.callerLastName == "כהן"
        assert payload.callerPhone1 == "0501234567"
        assert payload.callerEmail == ""  # Email not included
        assert payload.callerTZ == ""     # ID not included
        
        # Verify description
        assert payload.eventCallDesc == "פנס רחוב לא עובד ברחוב הרצל 5"
    
    def test_address_parsing(self):
        """Test address parsing into street components."""
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="מרים",
                last_name="לוי",
                phone="0521234567",
                email="miriam@example.com"
            ),
            category=IncidentCategory(
                name="ניקיון",
                description="Cleanliness and sanitation"
            ),
            description="זבל ברחוב",
            address="רחוב הרצל 15, נתניה"
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        
        # Verify address parsing
        assert payload.streetDesc == "הרצל"
        assert payload.houseNumber == "15"
        assert payload.streetCode == "123"  # Default/generated value


class TestCategoryMapping:
    """Test incident category mapping scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = PayloadTransformer()
    
    def test_lighting_category_mapping(self):
        """Test street lighting category mapping."""
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="דוד",
                last_name="סמית",
                phone="0531234567",
                email="david@example.com"
            ),
            category=IncidentCategory(
                name="תאורה",
                description="Street lighting issues"
            ),
            description="פנס רחוב שבור",
            address="רחוב ויצמן 10, נתניה"
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        
        # Verify category-specific transformations
        assert "תאורה" in payload.eventCallDesc or "פנס" in payload.eventCallDesc
    
    def test_cleanliness_category_mapping(self):
        """Test cleanliness category mapping."""
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="שרה",
                last_name="ברק",
                phone="0541234567",
                email="sarah@example.com"
            ),
            category=IncidentCategory(
                name="ניקיון",
                description="Cleanliness and sanitation"
            ),
            description="זבל בפארק העצמאות",
            address="פארק העצמאות, נתניה"
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        
        assert "זבל" in payload.eventCallDesc or "ניקיון" in payload.eventCallDesc
    
    def test_transportation_category_mapping(self):
        """Test transportation category mapping."""
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="אהרון",
                last_name="גולד",
                phone="0551234567",
                email="aaron@example.com"
            ),
            category=IncidentCategory(
                name="תחבורה",
                description="Transportation and traffic"
            ),
            description="בור בכביש ברחוב בן גוריון",
            address="רחוב בן גוריון 20, נתניה"
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        
        assert "תחבורה" in payload.eventCallDesc or "כביש" in payload.eventCallDesc or "בור" in payload.eventCallDesc
    
    def test_parks_category_mapping(self):
        """Test parks and landscaping category mapping."""
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="רחל",
                last_name="אבני",
                phone="0561234567",
                email="rachel@example.com"
            ),
            category=IncidentCategory(
                name="גינון",
                description="Parks and landscaping"
            ),
            description="עץ נפל בפארק",
            address="פארק נורדאו, נתניה"
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        
        assert "גינון" in payload.eventCallDesc or "עץ" in payload.eventCallDesc or "פארק" in payload.eventCallDesc
    
    def test_sidewalks_category_mapping(self):
        """Test sidewalks category mapping."""
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="משה",
                last_name="דהן",
                phone="0571234567",
                email="moshe@example.com"
            ),
            category=IncidentCategory(
                name="מדרכות",
                description="Sidewalks and walkways"
            ),
            description="מדרכה שבורה",
            address="רחוב רותשילד 30, נתניה"
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        
        assert "מדרכות" in payload.eventCallDesc or "מדרכה" in payload.eventCallDesc
    
    def test_other_category_mapping(self):
        """Test other category mapping."""
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="עינת",
                last_name="פרץ",
                phone="0581234567",
                email="einat@example.com"
            ),
            category=IncidentCategory(
                name="אחר",
                description="Other municipal issues"
            ),
            description="בעיה כללית ברחוב",
            address="רחוב דיזנגוף 40, נתניה"
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        
        assert "אחר" in payload.eventCallDesc or "בעיה" in payload.eventCallDesc


class TestAddressParsing:
    """Test various address parsing scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = PayloadTransformer()
    
    def test_simple_address_parsing(self):
        """Test simple address with street and number."""
        addresses = [
            ("רחוב הרצל 5, נתניה", "הרצל", "5"),
            ("רחוב בן גוריון 123, נתניה", "בן גוריון", "123"),
            ("רחוב ויצמן 7א, נתניה", "ויצמן", "7א"),
            ("שדרות דיזנגוף 45, נתניה", "דיזנגוף", "45"),
        ]
        
        for address, expected_street, expected_number in addresses:
            request = IncidentSubmissionRequest(
                user_data=UserData(
                    first_name="טסט",
                    last_name="יוזר",
                    phone="0501234567",
                    email="test@example.com"
                ),
                category=IncidentCategory(
                    name="אחר",
                    description="Other"
                ),
                description="תיאור בדיקה",
                address=address
            )
            
            payload = self.transformer.transform_to_api_payload(request)
            assert payload.streetDesc == expected_street
            assert payload.houseNumber == expected_number
    
    def test_complex_address_parsing(self):
        """Test complex address parsing scenarios."""
        complex_addresses = [
            ("רחוב יהודה הלוי 15 דירה 4, נתניה", "יהודה הלוי", "15"),
            ("שדרות דוד רמז 88 קומה 3, נתניה", "דוד רמז", "88"),
            ("רח' העצמאות 12ב, נתניה", "העצמאות", "12ב"),
        ]
        
        for address, expected_street, expected_number in complex_addresses:
            request = IncidentSubmissionRequest(
                user_data=UserData(
                    first_name="טסט",
                    last_name="יוזר",
                    phone="0501234567",
                    email="test@example.com"
                ),
                category=IncidentCategory(
                    name="אחר",
                    description="Other"
                ),
                description="תיאור בדיקה",
                address=address
            )
            
            payload = self.transformer.transform_to_api_payload(request)
            assert payload.streetDesc == expected_street
            assert payload.houseNumber == expected_number
    
    def test_address_without_number(self):
        """Test address parsing without house number."""
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="טסט",
                last_name="יוזר",
                phone="0501234567",
                email="test@example.com"
            ),
            category=IncidentCategory(
                name="אחר",
                description="Other"
            ),
            description="תיאור בדיקה",
            address="פארק העצמאות, נתניה"
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        assert payload.streetDesc == "העצמאות"
        assert payload.houseNumber == ""  # No number provided
    
    def test_malformed_address_handling(self):
        """Test handling of malformed addresses."""
        malformed_addresses = [
            "",                    # Empty address
            "נתניה",              # City only
            "123",                 # Number only
            "רחוב",               # Street word only
            "כתובת לא ברורה",     # Unclear address
        ]
        
        for address in malformed_addresses:
            request = IncidentSubmissionRequest(
                user_data=UserData(
                    first_name="טסט",
                    last_name="יוזר",
                    phone="0501234567",
                    email="test@example.com"
                ),
                category=IncidentCategory(
                    name="אחר",
                    description="Other"
                ),
                description="תיאור בדיקה",
                address=address
            )
            
            # Should not raise exception, but provide fallback values
            payload = self.transformer.transform_to_api_payload(request)
            assert payload.streetDesc is not None
            assert payload.houseNumber is not None
            assert payload.streetCode is not None


class TestUserDataMapping:
    """Test user data field mapping scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = PayloadTransformer()
    
    def test_complete_user_data_mapping(self):
        """Test complete user data mapping."""
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="אליה",
                last_name="בן-דוד",
                phone="0591234567",
                email="elijah@example.com"
            ),
            category=IncidentCategory(
                name="תאורה",
                description="Street lighting"
            ),
            description="פנס שבור",
            address="רחוב הרצל 10, נתניה"
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        
        assert payload.callerFirstName == "אליה"
        assert payload.callerLastName == "בן-דוד"
        assert payload.callerPhone1 == "0591234567"
        assert payload.callerEmail == ""  # Email excluded for privacy
        assert payload.callerTZ == ""     # ID excluded for privacy
    
    def test_special_characters_in_names(self):
        """Test names with special characters."""
        names_with_special_chars = [
            ("ג'ון", "סמית'"),           # Apostrophes
            ("מרי-אן", "בן-צבי"),        # Hyphens
            ("ז'אן", "ד'אר"),            # French-style names
            ("אברהם אברהם", "כהן לוי"),   # Space-separated compound names
        ]
        
        for first_name, last_name in names_with_special_chars:
            request = IncidentSubmissionRequest(
                user_data=UserData(
                    first_name=first_name,
                    last_name=last_name,
                    phone="0501234567",
                    email="test@example.com"
                ),
                category=IncidentCategory(
                    name="אחר",
                    description="Other"
                ),
                description="תיאור בדיקה",
                address="רחוב הרצל 1, נתניה"
            )
            
            payload = self.transformer.transform_to_api_payload(request)
            assert payload.callerFirstName == first_name
            assert payload.callerLastName == last_name
    
    def test_phone_number_formatting(self):
        """Test various phone number formats."""
        phone_formats = [
            "0501234567",      # Standard format
            "050-123-4567",    # With dashes (should be cleaned)
            "050 123 4567",    # With spaces (should be cleaned)
            "+972501234567",   # International format (should be normalized)
            "972501234567",    # International without +
        ]
        
        for phone in phone_formats:
            request = IncidentSubmissionRequest(
                user_data=UserData(
                    first_name="טסט",
                    last_name="יוזר",
                    phone=phone,
                    email="test@example.com"
                ),
                category=IncidentCategory(
                    name="אחר",
                    description="Other"
                ),
                description="תיאור בדיקה",
                address="רחוב הרצל 1, נתניה"
            )
            
            payload = self.transformer.transform_to_api_payload(request)
            # Phone should be normalized to standard Israeli format
            assert len(payload.callerPhone1) == 10
            assert payload.callerPhone1.startswith("05")


class TestDataSanitization:
    """Test data sanitization and security measures."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = PayloadTransformer()
    
    def test_html_injection_prevention(self):
        """Test prevention of HTML injection in text fields."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "Normal text <b>with html</b>",
            "Text with <!-- comment -->",
        ]
        
        for malicious_input in malicious_inputs:
            request = IncidentSubmissionRequest(
                user_data=UserData(
                    first_name="טסט",
                    last_name="יוזר",
                    phone="0501234567",
                    email="test@example.com"
                ),
                category=IncidentCategory(
                    name="אחר",
                    description="Other"
                ),
                description=malicious_input,
                address="רחוב הרצל 1, נתניה"
            )
            
            payload = self.transformer.transform_to_api_payload(request)
            # HTML tags should be escaped or removed
            assert "<script>" not in payload.eventCallDesc
            assert "onerror=" not in payload.eventCallDesc
    
    def test_sql_injection_prevention(self):
        """Test prevention of SQL injection attempts."""
        sql_injection_attempts = [
            "'; DROP TABLE incidents; --",
            "' OR '1'='1",
            "1; DELETE FROM users",
            "admin'--",
        ]
        
        for sql_input in sql_injection_attempts:
            request = IncidentSubmissionRequest(
                user_data=UserData(
                    first_name="טסט",
                    last_name=sql_input,  # Try injection in name field
                    phone="0501234567",
                    email="test@example.com"
                ),
                category=IncidentCategory(
                    name="אחר",
                    description="Other"
                ),
                description="תיאור רגיל",
                address="רחוב הרצל 1, נתניה"
            )
            
            payload = self.transformer.transform_to_api_payload(request)
            # SQL injection patterns should be neutralized
            assert "DROP TABLE" not in payload.callerLastName
            assert "--" not in payload.callerLastName
    
    def test_unicode_normalization(self):
        """Test Unicode text normalization."""
        unicode_texts = [
            "טקסט עם אותיות מיוחדות",       # Hebrew text
            "English with Hebrew עברית",    # Mixed languages
            "Numbers 123 and symbols !@#",  # Mixed content
            "דוגמה עם ציטוט \"כפול\"",      # Quotes
        ]
        
        for text in unicode_texts:
            request = IncidentSubmissionRequest(
                user_data=UserData(
                    first_name="טסט",
                    last_name="יוזר",
                    phone="0501234567",
                    email="test@example.com"
                ),
                category=IncidentCategory(
                    name="אחר",
                    description="Other"
                ),
                description=text,
                address="רחוב הרצל 1, נתניה"
            )
            
            payload = self.transformer.transform_to_api_payload(request)
            # Text should be properly normalized
            assert payload.eventCallDesc is not None
            assert len(payload.eventCallDesc) > 0


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = PayloadTransformer()
    
    def test_empty_or_minimal_data(self):
        """Test transformation with minimal valid data."""
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="א",  # Single character
                last_name="ב",   # Single character
                phone="0501234567",
                email="a@b.co"   # Minimal email
            ),
            category=IncidentCategory(
                name="אחר",
                description="Other"
            ),
            description="תיאור מינימלי קצר",  # Minimal description
            address="רחוב א 1, נתניה"       # Minimal address
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        
        # Should still produce valid payload
        assert payload.callerFirstName == "א"
        assert payload.callerLastName == "ב"
        assert payload.eventCallDesc == "תיאור מינימלי קצר"
    
    def test_maximum_length_data(self):
        """Test transformation with maximum length data."""
        max_description = "ת" * 1000  # Maximum allowed description
        max_name = "א" * 50           # Long name
        
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name=max_name,
                last_name=max_name,
                phone="0501234567",
                email="test@example.com"
            ),
            category=IncidentCategory(
                name="אחר",
                description="Other"
            ),
            description=max_description,
            address="רחוב עם שם ארוך מאוד מאוד 999, נתניה"
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        
        # Should handle long data appropriately
        assert payload.callerFirstName == max_name
        assert payload.eventCallDesc == max_description
    
    def test_null_or_none_handling(self):
        """Test handling of None values in optional fields."""
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="טסט",
                last_name="יוזר",
                phone="0501234567",
                email="test@example.com"
            ),
            category=IncidentCategory(
                name="אחר",
                description="Other"
            ),
            description="תיאור בדיקה",
            address="רחוב הרצל 1, נתניה",
            extra_files=None  # Explicitly None
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        
        # Should handle None values gracefully
        assert payload is not None
        assert payload.callerFirstName == "טסט"
    
    @patch('app.services.payload_transformation.logger')
    def test_transformation_logging(self, mock_logger):
        """Test that transformation events are logged."""
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="טסט",
                last_name="יוזר",
                phone="0501234567",
                email="test@example.com"
            ),
            category=IncidentCategory(
                name="אחר",
                description="Other"
            ),
            description="תיאור בדיקה",
            address="רחוב הרצל 1, נתניה"
        )
        
        payload = self.transformer.transform_to_api_payload(request)
        
        # Verify logging occurred
        assert mock_logger.debug.called or mock_logger.info.called
        assert payload is not None
    
    def test_transformation_consistency(self):
        """Test that repeated transformations produce consistent results."""
        request = IncidentSubmissionRequest(
            user_data=UserData(
                first_name="טסט",
                last_name="יוזר",
                phone="0501234567",
                email="test@example.com"
            ),
            category=IncidentCategory(
                name="תאורה",
                description="Street lighting"
            ),
            description="פנס שבור ברחוב הרצל",
            address="רחוב הרצל 15, נתניה"
        )
        
        # Transform multiple times
        payload1 = self.transformer.transform_to_api_payload(request)
        payload2 = self.transformer.transform_to_api_payload(request)
        payload3 = self.transformer.transform_to_api_payload(request)
        
        # Results should be identical
        assert payload1.model_dump() == payload2.model_dump()
        assert payload2.model_dump() == payload3.model_dump()
    
    def test_concurrent_transformations(self):
        """Test concurrent transformation operations."""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def transform_request(request_number):
            try:
                request = IncidentSubmissionRequest(
                    user_data=UserData(
                        first_name=f"טסט{request_number}",
                        last_name="יוזר",
                        phone="0501234567",
                        email="test@example.com"
                    ),
                    category=IncidentCategory(
                        name="אחר",
                        description="Other"
                    ),
                    description=f"תיאור בדיקה מספר {request_number}",
                    address="רחוב הרצל 1, נתניה"
                )
                
                payload = self.transformer.transform_to_api_payload(request)
                results_queue.put((request_number, payload.callerFirstName))
            except Exception as e:
                results_queue.put((request_number, f"ERROR: {e}"))
        
        # Start multiple transformation threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=transform_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check all transformations succeeded
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == 5
        for request_number, first_name in results:
            assert not first_name.startswith("ERROR")
            assert first_name == f"טסט{request_number}"
