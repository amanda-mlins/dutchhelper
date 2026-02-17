import logging
import pysbd
from typing import List

logger = logging.getLogger(__name__)

class NLPService:
    """Service for Natural Language Processing tasks using pysbd"""
    
    _segmenter = None

    @classmethod
    def get_segmenter(cls):
        """
        Get or initialize the pysbd segmenter for Dutch.
        Uses a singleton pattern to avoid re-initializing.
        """
        if cls._segmenter is None:
            logger.info("Initializing pysbd Segmenter for Dutch ('nl')...")
            # pysbd handles common abbreviations and sentence boundaries well
            # The 'language' parameter uses language-specific rules for Dutch
            cls._segmenter = pysbd.Segmenter(language="nl", clean=False)
        return cls._segmenter

    @classmethod
    def split_sentences(cls, text: str, deduplicate: bool = True) -> List[str]:
        """
        Split Dutch text into sentences using pysbd.
        Handles abbreviations like 'a.u.b.', 'e.g.', 'dr.', etc.
        
        Args:
            text: Dutch text to split
            deduplicate: If True, remove duplicate sentences (default: True)
            
        Returns:
            List of sentence strings (deduplicated if requested)
        """
        if not text or not text.strip():
            return []
            
        segmenter = cls.get_segmenter()
        sentences = segmenter.segment(text)
        
        # Clean up each sentence and filter out empty strings
        cleaned_sentences = [s.strip() for s in sentences if s.strip()]
        
        # Deduplicate while preserving order
        if deduplicate:
            unique_sentences = []
            seen = set()
            for sentence in cleaned_sentences:
                # Case-insensitive deduplication to catch "Hello." vs "hello."
                lower_sentence = sentence.lower()
                if lower_sentence not in seen:
                    seen.add(lower_sentence)
                    unique_sentences.append(sentence)
            cleaned_sentences = unique_sentences
            
            if logger.isEnabledFor(logging.DEBUG):
                removed_count = len(sentences) - len(cleaned_sentences)
                if removed_count > 0:
                    logger.debug(f"Removed {removed_count} duplicate sentences")
        
        logger.debug(f"Split text into {len(cleaned_sentences)} sentences using pysbd")
        return cleaned_sentences
