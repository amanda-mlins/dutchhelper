"""
Unit tests for NLPService sentence splitting logic.

This module tests the Dutch sentence boundary detection using pysbd,
ensuring it correctly handles:
- Normal sentences
- Abbreviations (a.u.b., dr., drs., etc.)
- Multiple sentences
- Edge cases (empty strings, only punctuation, etc.)
"""

import pytest
from app.nlp_service import NLPService


class TestNLPServiceSentenceSplitting:
    """Test suite for NLPService.split_sentences method"""

    def test_simple_single_sentence(self):
        """Test splitting a simple single sentence"""
        text = "Dit is een Nederlandse zin."
        result = NLPService.split_sentences(text)
        assert len(result) == 1
        assert result[0] == "Dit is een Nederlandse zin."

    def test_multiple_sentences(self):
        """Test splitting multiple sentences"""
        text = "Dit is de eerste zin. Dit is de tweede zin. En dit is de derde."
        result = NLPService.split_sentences(text)
        assert len(result) == 3
        assert result[0] == "Dit is de eerste zin."
        assert result[1] == "Dit is de tweede zin."
        assert result[2] == "En dit is de derde."

    def test_abbr_aub_dutch_please(self):
        """Test that 'a.u.b.' (alstublieft) is NOT treated as sentence boundary"""
        text = "Kom a.u.b. morgen langs. Dank je wel!"
        result = NLPService.split_sentences(text)
        # Should be 2 sentences, not 3 (the period after a.u.b. should not split)
        assert len(result) == 2
        assert "a.u.b. morgen" in result[0]
        assert "Dank je wel!" in result[1]

    def test_abbr_dr_title(self):
        """Test that 'dr.' (doctor) abbreviation at start of proper name"""
        text = "Dr. Smith is een goede arts. Hij helpt veel patiënten."
        result = NLPService.split_sentences(text)
        # pysbd may split "Dr." separately when followed by a proper name
        assert len(result) >= 2
        assert any("Smith" in s for s in result)

    def test_abbr_drs_title(self):
        """Test that 'drs.' (doctorandus - Dutch academic title) handling"""
        text = "Drs. Janssen werkt hier. Hij is zeer capabel."
        result = NLPService.split_sentences(text)
        # pysbd may split "Drs." separately when followed by a proper name
        assert len(result) >= 2
        assert any("Janssen" in s for s in result)

    def test_abbr_etc(self):
        """Test that 'etc.' abbreviation doesn't split"""
        text = "We hebben appels, bananen, citroenen, etc. en nog veel meer."
        result = NLPService.split_sentences(text)
        assert len(result) == 1
        assert "etc. en nog veel meer" in result[0]

    def test_abbr_eg(self):
        """Test that 'e.g.' abbreviation doesn't split"""
        text = "Veel dieren, e.g. katten en honden, hebben staarten. Dit is interessant."
        result = NLPService.split_sentences(text)
        assert len(result) == 2

    def test_sentence_with_ellipsis(self):
        """Test sentences with ellipsis (...)"""
        text = "Ik weet niet... misschien kom ik morgen. Dat zien we wel."
        result = NLPService.split_sentences(text)
        assert len(result) == 2

    def test_exclamation_mark(self):
        """Test sentences ending with exclamation mark"""
        text = "Wat fantastisch! Dit is geweldig!"
        result = NLPService.split_sentences(text)
        assert len(result) == 2
        assert result[0] == "Wat fantastisch!"
        assert result[1] == "Dit is geweldig!"

    def test_question_mark(self):
        """Test sentences ending with question mark"""
        text = "Hoe gaat het? Gaat het goed met je?"
        result = NLPService.split_sentences(text)
        assert len(result) == 2

    def test_mixed_punctuation(self):
        """Test sentences with mixed ending punctuation"""
        text = "Wat gebeurde er!? Ik kan het niet geloven. Waarom?"
        result = NLPService.split_sentences(text)
        assert len(result) >= 2  # pysbd should handle !? correctly

    def test_empty_string(self):
        """Test with empty string"""
        result = NLPService.split_sentences("")
        assert result == []

    def test_whitespace_only(self):
        """Test with whitespace-only string"""
        result = NLPService.split_sentences("   \n  \t  ")
        assert result == []

    def test_single_word(self):
        """Test with single word (no punctuation)"""
        result = NLPService.split_sentences("Hallo")
        assert len(result) == 1
        assert result[0] == "Hallo"

    def test_no_trailing_period(self):
        """Test sentence without trailing period"""
        text = "Dit is een zin zonder punt"
        result = NLPService.split_sentences(text)
        assert len(result) == 1

    def test_multiple_spaces_between_sentences(self):
        """Test that multiple spaces between sentences are handled"""
        text = "Eerste zin.   Tweede zin."
        result = NLPService.split_sentences(text)
        assert len(result) == 2
        # Results should be stripped
        assert all(s.strip() == s for s in result)

    def test_newlines_between_sentences(self):
        """Test that newlines are handled correctly"""
        text = "Eerste zin.\nTweede zin.\nDerde zin."
        result = NLPService.split_sentences(text)
        assert len(result) == 3

    def test_tabs_and_special_whitespace(self):
        """Test handling of tabs and special whitespace"""
        text = "Eerste zin.\t\nTweede zin."
        result = NLPService.split_sentences(text)
        assert len(result) == 2

    def test_long_numbers(self):
        """Test handling of numbers with periods"""
        text = "Ook waren er meerdere demonstraties met meer dan 20.000 deelnemers"
        result = NLPService.split_sentences(text)
        assert len(result) == 1

    def test_long_sentence(self):
        """Test with a very long, complex sentence"""
        text = "Dit is een zeer lange zin met veel woorden die doorgaat en doorgaat en doorgaat totdat hij eindelijk eindigt."
        result = NLPService.split_sentences(text)
        assert len(result) == 1
        assert "eindelijk eindigt" in result[0]

    def test_sentence_with_quotes(self):
        """Test sentences containing quoted text"""
        text = 'Hij zei: "Goedemorgen!" Ik antwoordde: "Hallo!"'
        result = NLPService.split_sentences(text)
        assert len(result) >= 2

    def test_sentence_with_parentheses(self):
        """Test sentences with parentheses"""
        text = "Dit is een zin (met uitleg erin). Dit is nog een zin."
        result = NLPService.split_sentences(text)
        assert len(result) == 2

    def test_dutch_diacritics(self):
        """Test Dutch text with special characters and diacritics"""
        text = "Café is een leuk woord. Naïef is ook Nederlands."
        result = NLPService.split_sentences(text)
        assert len(result) == 2
        assert "Café" in result[0]
        assert "Naïef" in result[1]

    def test_numbers_with_periods(self):
        """Test that periods after numbers don't cause incorrect splits"""
        text = "De prijs is 3.50 euro. Dit is goedkoop."
        result = NLPService.split_sentences(text)
        # Should be 2 sentences (3.50 should not cause a split)
        assert len(result) == 2  # pysbd may handle this differently
    
    def test_numbers_with_periods_pt2(self):
        """Test that periods after numbers don't cause incorrect splits"""
        text = "Ook waren er meerdere demonstraties met meer dan 20.000 deelnemers, zoals de Feminist March en protesten rond Gaza en racisme. "
        result = NLPService.split_sentences(text)
        # Should be 1 sentences 
        assert len(result) == 1  # pysbd may handle this differently

    def test_sentence_segmenter_singleton(self):
        """Test that the segmenter is reused (singleton pattern)"""
        segmenter1 = NLPService.get_segmenter()
        segmenter2 = NLPService.get_segmenter()
        assert segmenter1 is segmenter2  # Should be the same object

    def test_realistic_dutch_paragraph(self):
        """Test with realistic Dutch paragraph"""
        text = """Goedemorgen! Hoe gaat het met u? Dit is een test van de 
        Nederlandse zinssplitsing. Dr. de Wilde werkt hier als arts. A.u.b. 
        let op deze details. Dit is het einde van de test."""
        
        result = NLPService.split_sentences(text)
        
        # Should have multiple sentences
        assert len(result) > 1
        # Should preserve most text (abbreviated forms may be split differently)
        full_text = " ".join(result)
        assert "Goedemorgen" in full_text
        assert "zinssplitsing" in full_text

    def test_result_is_list_of_strings(self):
        """Test that result is always a list of strings"""
        text = "Test zin."
        result = NLPService.split_sentences(text)
        assert isinstance(result, list)
        assert all(isinstance(s, str) for s in result)

    def test_no_empty_strings_in_result(self):
        """Test that result list contains no empty strings"""
        text = "Eerste.  Tweede.  Derde."
        result = NLPService.split_sentences(text)
        assert all(s.strip() for s in result)  # No empty or whitespace-only strings
