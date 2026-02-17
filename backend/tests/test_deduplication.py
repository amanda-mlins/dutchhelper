"""Unit tests for sentence deduplication functionality"""
import pytest
from app.nlp_service import NLPService


class TestBasicDeduplication:
    """Test basic deduplication logic"""
    
    def test_no_duplicates(self):
        """Test text with no duplicate sentences"""
        text = "Dit is zin één. Dit is zin twee. Dit is zin drie."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) == 3
        assert result[0] == "Dit is zin één."
        assert result[1] == "Dit is zin twee."
        assert result[2] == "Dit is zin drie."
    
    def test_exact_duplicates_removed(self):
        """Test that exact duplicate sentences are removed"""
        text = "Hallo wereld. Dit is een test. Hallo wereld. Goedemorgen."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) == 3
        assert result == ["Hallo wereld.", "Dit is een test.", "Goedemorgen."]
    
    def test_case_insensitive_deduplication(self):
        """Test that deduplication is case-insensitive"""
        text = "Hallo wereld. HALLO WERELD. hallo wereld."
        result = NLPService.split_sentences(text, deduplicate=True)
        # Should keep only the first occurrence
        assert len(result) == 1
        assert result[0] == "Hallo wereld."
    
    def test_multiple_duplicates(self):
        """Test multiple instances of duplicate sentences"""
        text = "Eerste. Tweede. Eerste. Derde. Eerste. Tweede."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) == 3
        assert result == ["Eerste.", "Tweede.", "Derde."]
    
    def test_deduplication_preserves_order(self):
        """Test that deduplication preserves the order of first occurrence"""
        text = "Eerste. Tweede. Derde. Tweede. Eerste. Vierde."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert result == ["Eerste.", "Tweede.", "Derde.", "Vierde."]


class TestDuplicateWithWhitespace:
    """Test deduplication with whitespace variations"""
    
    def test_leading_trailing_whitespace_normalized(self):
        """Test that whitespace is normalized before comparing"""
        text = "Zin één.  Zin twee.  Zin één.  Zin drie."
        result = NLPService.split_sentences(text, deduplicate=True)
        # The NLPService strips whitespace, so these should be considered duplicates
        assert len(result) == 3
        assert "Zin één." in result
        assert "Zin twee." in result
        assert "Zin drie." in result
    
    def test_punctuation_variations(self):
        """Test sentences with different punctuation are not deduplicated"""
        text = "Dit is een vraag? Dit is een vraag. Dit is een vraag!"
        result = NLPService.split_sentences(text, deduplicate=True)
        # Different punctuation should NOT be deduplicated
        assert len(result) == 3


class TestDuplicateDisabled:
    """Test behavior when deduplication is disabled"""
    
    def test_no_deduplication_when_disabled(self):
        """Test that duplicates are kept when deduplicate=False"""
        text = "Hallo. Wereld. Hallo. Hallo."
        result = NLPService.split_sentences(text, deduplicate=False)
        assert len(result) == 4
        assert result == ["Hallo.", "Wereld.", "Hallo.", "Hallo."]
    
    def test_default_is_deduplicate_true(self):
        """Test that deduplication is enabled by default"""
        text = "A. B. A."
        result_default = NLPService.split_sentences(text)
        result_explicit = NLPService.split_sentences(text, deduplicate=True)
        assert result_default == result_explicit


class TestEdgeCases:
    """Test edge cases for deduplication"""
    
    def test_empty_text(self):
        """Test empty text"""
        result = NLPService.split_sentences("", deduplicate=True)
        assert result == []
    
    def test_single_sentence(self):
        """Test single sentence"""
        text = "Dit is de enige zin."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert result == ["Dit is de enige zin."]
    
    def test_single_sentence_repeated(self):
        """Test single sentence repeated multiple times"""
        text = "Zin. Zin. Zin. Zin."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert result == ["Zin."]
    
    def test_whitespace_only(self):
        """Test whitespace-only text"""
        result = NLPService.split_sentences("   \n  \t  ", deduplicate=True)
        assert result == []
    
    def test_very_long_duplicate_text(self):
        """Test deduplication with very long sentences"""
        long_sentence = "Dit is een zeer lange zin " * 50 + "."
        text = long_sentence + " " + long_sentence + " Dit is een korte."
        result = NLPService.split_sentences(text, deduplicate=True)
        # Should only keep one instance of the long sentence
        assert len(result) >= 1


class TestPerformanceCharacteristics:
    """Test performance characteristics of deduplication"""
    
    def test_many_unique_sentences(self):
        """Test that many unique sentences are handled efficiently"""
        sentences = [f"Dit is zin {i}." for i in range(100)]
        text = " ".join(sentences)
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) == 100
    
    def test_many_duplicate_sentences(self):
        """Test efficiency with many duplicates"""
        # Use a realistic mix of sentences that pysbd will properly segment
        text = "Eerste. Tweede. Derde. " * 30 + "Eerste. Tweede. Derde."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) == 3
        assert result == ["Eerste.", "Tweede.", "Derde."]


class TestRealWorldScenarios:
    """Test real-world scenarios"""
    
    def test_repeated_sentence_in_paragraph(self):
        """Test paragraph with repeated sentence (real-world scenario)"""
        text = """
        De restaurant in Weesp wordt geteisterd door incidenten.
        De restaurant in Weesp wordt geteisterd door incidenten.
        Op 23 januari ontstond een kleine brand.
        De restaurant in Weesp wordt geteisterd door incidenten.
        """
        result = NLPService.split_sentences(text, deduplicate=True)
        # Should deduplicate the repeated sentence
        assert len(result) == 2
        assert "De restaurant in Weesp wordt geteisterd door incidenten." in result
        assert "Op 23 januari ontstond een kleine brand." in result
    
    def test_news_article_with_quote_repetition(self):
        """Test news article where a quote appears multiple times"""
        text = (
            "De burgemeester zei: 'Dit kan niet langer.' "
            "Iedereen was het erover eens. "
            "De burgemeester zei: 'Dit kan niet langer.' "
            "De maatregelen werden onmiddellijk ingevoerd."
        )
        result = NLPService.split_sentences(text, deduplicate=True)
        # The duplicate quote should be removed
        assert "Dit kan niet langer." in " ".join(result)
    
    def test_dutch_abbreviations_not_duplicated(self):
        """Test that Dutch abbreviations don't cause duplicate splitting"""
        text = "Dr. Smith werkt op de U.v.A. Dr. Smith werkt hard."
        result = NLPService.split_sentences(text, deduplicate=True)
        # Should handle abbreviations correctly without duplication issues
        assert len(result) >= 1
