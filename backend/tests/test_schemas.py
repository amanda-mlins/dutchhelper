"""
Unit tests for Pydantic schemas and data validation.
"""

import pytest
from pydantic import ValidationError
from app.schemas import (
    Message,
    SentenceComponent,
    SentenceAnalysis,
    TextAnalysisRequest,
    AnalyzeSentenceRequest,
    TextAnalysisResponse,
)


class TestMessageSchema:
    """Test suite for Message schema"""

    def test_message_creation_with_defaults(self):
        """Test Message creation with default status"""
        msg = Message(text="Hello")
        assert msg.text == "Hello"
        assert msg.status == "success"

    def test_message_creation_with_custom_status(self):
        """Test Message creation with custom status"""
        msg = Message(text="Hello", status="pending")
        assert msg.text == "Hello"
        assert msg.status == "pending"

    def test_message_validation_requires_text(self):
        """Test that Message requires text field"""
        with pytest.raises(ValidationError):
            Message()

    def test_message_empty_text(self):
        """Test Message with empty text"""
        msg = Message(text="")
        assert msg.text == ""


class TestSentenceComponentSchema:
    """Test suite for SentenceComponent schema"""

    def test_component_creation_minimal(self):
        """Test SentenceComponent with minimal required fields"""
        component = SentenceComponent(
            type="noun",
            value="kat",
            position=0
        )
        assert component.type == "noun"
        assert component.value == "kat"
        assert component.position == 0
        assert component.translation is None
        assert component.details is None

    def test_component_creation_with_all_fields(self):
        """Test SentenceComponent with all fields"""
        component = SentenceComponent(
            type="noun",
            value="kat",
            position=0,
            translation="cat",
            details={"gender": "feminine", "de_or_het": "de"}
        )
        assert component.type == "noun"
        assert component.translation == "cat"
        assert component.details["gender"] == "feminine"

    def test_component_validation_requires_type(self):
        """Test that SentenceComponent requires type"""
        with pytest.raises(ValidationError):
            SentenceComponent(value="test", position=0)

    def test_component_validation_requires_value(self):
        """Test that SentenceComponent requires value"""
        with pytest.raises(ValidationError):
            SentenceComponent(type="noun", position=0)

    def test_component_validation_requires_position(self):
        """Test that SentenceComponent requires position"""
        with pytest.raises(ValidationError):
            SentenceComponent(type="noun", value="test")

    def test_component_position_can_be_zero(self):
        """Test that position can be 0"""
        component = SentenceComponent(type="noun", value="test", position=0)
        assert component.position == 0

    def test_component_position_negative(self):
        """Test that position can be negative (though unusual)"""
        component = SentenceComponent(type="noun", value="test", position=-1)
        assert component.position == -1


class TestSentenceAnalysisSchema:
    """Test suite for SentenceAnalysis schema"""

    def test_sentence_analysis_minimal(self):
        """Test SentenceAnalysis with minimal fields"""
        analysis = SentenceAnalysis(sentence="Dit is een zin.")
        assert analysis.sentence == "Dit is een zin."
        assert analysis.sentence_translation is None
        assert analysis.components == []

    def test_sentence_analysis_with_translation(self):
        """Test SentenceAnalysis with translation"""
        analysis = SentenceAnalysis(
            sentence="Hallo!",
            sentence_translation="Hello!"
        )
        assert analysis.sentence == "Hallo!"
        assert analysis.sentence_translation == "Hello!"

    def test_sentence_analysis_with_components(self):
        """Test SentenceAnalysis with components"""
        component = SentenceComponent(
            type="noun",
            value="kat",
            position=0,
            translation="cat"
        )
        analysis = SentenceAnalysis(
            sentence="De kat zit.",
            components=[component]
        )
        assert len(analysis.components) == 1
        assert analysis.components[0].value == "kat"

    def test_sentence_analysis_validation_requires_sentence(self):
        """Test that SentenceAnalysis requires sentence"""
        with pytest.raises(ValidationError):
            SentenceAnalysis()


class TestTextAnalysisRequestSchema:
    """Test suite for TextAnalysisRequest schema"""

    def test_text_analysis_request_creation(self):
        """Test TextAnalysisRequest creation"""
        request = TextAnalysisRequest(text="Dit is een test.")
        assert request.text == "Dit is een test."

    def test_text_analysis_request_validation_requires_text(self):
        """Test that TextAnalysisRequest requires text"""
        with pytest.raises(ValidationError):
            TextAnalysisRequest()

    def test_text_analysis_request_empty_text(self):
        """Test TextAnalysisRequest with empty text"""
        request = TextAnalysisRequest(text="")
        assert request.text == ""


class TestAnalyzeSentenceRequestSchema:
    """Test suite for AnalyzeSentenceRequest schema"""

    def test_analyze_sentence_request_creation(self):
        """Test AnalyzeSentenceRequest creation"""
        request = AnalyzeSentenceRequest(sentence="Dit is een zin.")
        assert request.sentence == "Dit is een zin."

    def test_analyze_sentence_request_validation_requires_sentence(self):
        """Test that AnalyzeSentenceRequest requires sentence"""
        with pytest.raises(ValidationError):
            AnalyzeSentenceRequest()

    def test_analyze_sentence_request_empty_sentence(self):
        """Test AnalyzeSentenceRequest with empty sentence"""
        request = AnalyzeSentenceRequest(sentence="")
        assert request.sentence == ""


class TestTextAnalysisResponseSchema:
    """Test suite for TextAnalysisResponse schema"""

    def test_response_creation_minimal(self):
        """Test TextAnalysisResponse with minimal fields"""
        response = TextAnalysisResponse(original_text="Test")
        assert response.original_text == "Test"
        assert response.sentences == []
        assert response.summary is None

    def test_response_creation_with_sentences(self):
        """Test TextAnalysisResponse with sentences"""
        analysis = SentenceAnalysis(sentence="Dit is een zin.")
        response = TextAnalysisResponse(
            original_text="Dit is een zin.",
            sentences=[analysis]
        )
        assert len(response.sentences) == 1
        assert response.sentences[0].sentence == "Dit is een zin."

    def test_response_creation_with_summary(self):
        """Test TextAnalysisResponse with summary"""
        response = TextAnalysisResponse(
            original_text="Test",
            summary={"word_count": 1, "sentence_count": 1}
        )
        assert response.summary["word_count"] == 1

    def test_response_validation_requires_original_text(self):
        """Test that TextAnalysisResponse requires original_text"""
        with pytest.raises(ValidationError):
            TextAnalysisResponse()

    def test_response_empty_original_text(self):
        """Test TextAnalysisResponse with empty original_text"""
        response = TextAnalysisResponse(original_text="")
        assert response.original_text == ""
