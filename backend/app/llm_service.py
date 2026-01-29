"""LLM service for OpenRouter integration"""
import logging
import os
import httpx
import json
from typing import Optional
from app.models import SentenceComponent, SentenceAnalysis
from app.exceptions import ProcessingError

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "mistralai/mistral-nemo"

class OpenRouterService:
    """Service for interacting with OpenRouter LLM"""
    
    @staticmethod
    async def analyze_dutch_text(text: str) -> list[SentenceAnalysis]:
        """
        Analyze Dutch text using OpenRouter LLM.
        
        Args:
            text: Dutch text to analyze
            
        Returns:
            List of SentenceAnalysis with grammatical components
            
        Raises:
            ProcessingError: If LLM call fails
        """
        if not OPENROUTER_API_KEY:
            raise ProcessingError("OPENROUTER_API_KEY environment variable not set")
        
        try:
            logger.info(f"[OpenRouter] Starting analysis of text: {text[:100]}...")
            
            # Split text into sentences first
            sentences = OpenRouterService._split_sentences(text)
            logger.info(f"[OpenRouter] Split text into {len(sentences)} sentence(s)")
            
            analyzed_sentences = []
            
            for idx, sentence in enumerate(sentences, 1):
                logger.info(f"[OpenRouter] Processing sentence {idx}/{len(sentences)}")
                analysis = await OpenRouterService._analyze_sentence(sentence)
                analyzed_sentences.append(analysis)
            
            logger.info(f"[OpenRouter] Analysis complete. Processed {len(analyzed_sentences)} sentences")
            return analyzed_sentences
            
        except Exception as e:
            logger.error(f"[OpenRouter] Error analyzing text with OpenRouter: {str(e)}", exc_info=True)
            raise ProcessingError(f"Failed to analyze text: {str(e)}")
    
    @staticmethod
    async def _analyze_sentence(sentence: str) -> SentenceAnalysis:
        """
        Analyze a single sentence for grammatical components using OpenRouter.
        
        Args:
            sentence: Sentence to analyze
            
        Returns:
            SentenceAnalysis with extracted components
        """
        logger.info(f"[OpenRouter] Analyzing sentence: {sentence}")
        prompt = OpenRouterService._build_analysis_prompt(sentence)
        logger.debug(f"[OpenRouter] Prompt: {prompt[:200]}...")  # First 200 chars
        
        async with httpx.AsyncClient() as client:
            logger.info(f"[OpenRouter] Sending request to {OPENROUTER_BASE_URL} with model: {MODEL}")
            response = await client.post(
                OPENROUTER_BASE_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://dutchhelper.ai",
                    "X-Title": "DutchHelper",
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,  # Low temperature for consistent results
                    "max_tokens": 2000,
                },
            )
            
            logger.info(f"[OpenRouter] Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"[OpenRouter] API error: {response.status_code} - {response.text}")
                raise ProcessingError(f"OpenRouter API error: {response.status_code}")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            logger.debug(f"[OpenRouter] LLM response sample: {content[:100]}")  # Sample content
            
            # Parse the LLM response
            components, sentence_translation = OpenRouterService._parse_llm_response(content, sentence)
            
            logger.info(f"[OpenRouter] Extracted {len(components)} components from sentence")
            for i, component in enumerate(components, 1):
                logger.debug(f"  [{i}] {component.type}: '{component.value}'")
            
            return SentenceAnalysis(
                sentence=sentence,
                sentence_translation=sentence_translation,
                components=components
            )
    
    @staticmethod
    def _build_analysis_prompt(sentence: str) -> str:
        """
        Build the prompt for analyzing a Dutch sentence.
        
        Args:
            sentence: The sentence to analyze
            
        Returns:
            Prompt string for the LLM
        """
        return f"""Analyze this Dutch sentence and extract grammatical components in JSON format.

Sentence: "{sentence}"

For each word or phrase, identify its grammatical role. Return a JSON object with:
- "sentence_translation": the English translation of the entire sentence
- "components": JSON array with objects containing:
  - "word": the word or phrase
  - "type": the grammatical type (subject, verb, object, adjective, article, noun, adverb, preposition, conjunction, etc.)
  - "position": the starting character position in the sentence
  - "translation": the English translation of the word or phrase
  - "details": additional relevant grammatical information, for example verb infinitive form and verb tense used, make sure to check separable verbs and multi-word expressions.


Format expected:
{{
  "sentence_translation": "The cat sits on the table.",
  "components": [
    {{"word": "De", "type": "article", "position": 0, "translation": "The", "details": {{"article-type": "definite"}}}},
    {{"word": "kat", "type": "noun", "position": 3, "translation": "cat", "details": {{"noun-gender": "feminine", "de-or-het": "de"}}}},
    {{"word": "zit", "type": "verb", "position": 7, "translation": "sits", "details": {{"verb-tense": "present", "infinitive": "zitten"}}}},
    {{"word": "op", "type": "preposition", "position": 11, "translation": "on", "details": {{"preposition-type": "directional"}}}},
    {{"word": "de", "type": "article", "position": 14, "translation": "the", "details": {{"article-type": "definite"}}}},
    {{"word": "tafel", "type": "noun", "position": 17, "translation": "table", "details": {{"noun-gender": "feminine", "de-or-het": "de"}}}}
  ]
}}

Return only the JSON object, no other text. Make sure JSON is properly formatted."""

    @staticmethod
    def _parse_llm_response(content: str, sentence: str) -> tuple[list[SentenceComponent], str]:
        """
        Parse the LLM response and extract grammatical components and sentence translation.
        
        Args:
            content: The LLM response content
            sentence: The original sentence (for validation)
            
        Returns:
            Tuple of (List of SentenceComponent objects, sentence translation)
        """
        try:
            # Extract JSON from response (handle cases where LLM adds extra text)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning(f"[OpenRouter] Could not find JSON in LLM response: {content}")
                return [], None
            
            json_str = content[json_start:json_end]
            logger.debug(f"[OpenRouter] Extracted JSON sample: {json_str[:15]}...")
            
            response_data = json.loads(json_str)
            logger.debug(f"[OpenRouter] Parsed response data")
            
            # Extract sentence translation
            sentence_translation = response_data.get("sentence_translation")
            logger.info(f"[OpenRouter] Sentence translation: {sentence_translation}")
            
            # Extract components
            components_data = response_data.get("components", [])
            logger.debug(f"[OpenRouter] Parsed {len(components_data)} components from JSON")
            
            components = []
            for item in components_data:
                if isinstance(item, dict) and "word" in item and "type" in item:
                    components.append(
                        SentenceComponent(
                            type=item["type"],
                            value=item["word"],
                            position=item.get("position", 0),
                            translation=item.get("translation"),
                            details=item.get("details")
                        )
                    )
            
            logger.debug(f"[OpenRouter] Successfully created {len(components)} SentenceComponent objects")
            return components, sentence_translation
            
        except json.JSONDecodeError as e:
            logger.warning(f"[OpenRouter] Failed to parse JSON from LLM response: {e}")
            logger.debug(f"[OpenRouter] Content that failed to parse: {content}")
            return [], None
    
    @staticmethod
    def _is_valid_sentence(sentence: str) -> bool:
        """
        Check if a sentence is valid (contains at least one word).
        
        A valid sentence must:
        - Have at least one word (letter sequence)
        - Not be just punctuation, numbers, or whitespace
        
        Args:
            sentence: Sentence to validate
            
        Returns:
            True if sentence is valid, False otherwise
        """
        import re
        # Check if sentence contains at least one word (sequence of letters)
        # This pattern matches any word character sequence (including accents for Dutch)
        has_word = re.search(r'[a-zA-Z\u00C0-\u00FF]+', sentence)
        
        if has_word:
            logger.debug(f"[OpenRouter] Valid sentence: '{sentence}'")
            return True
        else:
            logger.debug(f"[OpenRouter] Filtered out invalid sentence: '{sentence}'")
            return False
    
    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """
        Split text into sentences and filter for valid ones.
        
        Args:
            text: Text to split
            
        Returns:
            List of valid sentences (containing at least one word)
        """
        import re
        # Split by common sentence-ending punctuation
        sentences = re.split(r'[.!?]+', text)
        
        # Clean and filter sentences
        valid_sentences = [
            s.strip() 
            for s in sentences 
            if s.strip() and OpenRouterService._is_valid_sentence(s.strip())
        ]
        
        logger.debug(f"[OpenRouter] Split text into {len(valid_sentences)} valid sentence(s) from {len([s.strip() for s in sentences if s.strip()])} total")
        return valid_sentences
