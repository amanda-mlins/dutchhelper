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
    def split_sentences(cls, text: str) -> List[str]:
        """
        Split Dutch text into sentences using pysbd.
        Handles abbreviations like 'a.u.b.', 'e.g.', 'dr.', etc.
        
        Args:
            text: Dutch text to split
            
        Returns:
            List of sentence strings
        """
        if not text or not text.strip():
            return []
            
        segmenter = cls.get_segmenter()
        sentences = segmenter.segment(text)
        
        # Clean up each sentence and filter out empty strings
        cleaned_sentences = [s.strip() for s in sentences if s.strip()]
        
        logger.debug(f"Split text into {len(cleaned_sentences)} sentences using pysbd")
        return cleaned_sentences
