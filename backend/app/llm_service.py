"""LLM service for OpenRouter integration"""
import logging
import os
import httpx
import json
from typing import Optional, List
from app.schemas import SentenceComponent, SentenceAnalysis
from app.exceptions import ProcessingError
from app.config import settings
from app.nlp_service import NLPService

logger = logging.getLogger(__name__)

class OpenRouterService:
    """Service for interacting with OpenRouter LLM"""
    
    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        """Get or create a singleton httpx client"""
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.AsyncClient(
                base_url="https://openrouter.ai/api/v1",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://dutchhelper.ai",
                    "X-Title": "DutchHelper",
                },
                timeout=httpx.Timeout(60.0)
            )
        return cls._client

    @staticmethod
    async def analyze_dutch_text(text: str) -> List[SentenceAnalysis]:
        """
        Analyze Dutch text using OpenRouter LLM.
        
        Args:
            text: Dutch text to analyze
            
        Returns:
            List of SentenceAnalysis with grammatical components
            
        Raises:
            ProcessingError: If LLM call fails
        """
        if not settings.OPENROUTER_API_KEY:
            raise ProcessingError("OPENROUTER_API_KEY environment variable not set")
        
        try:
            logger.info(f"[OpenRouter] Starting analysis of text: {text[:100]}...")
            
            # Use NLPService for robust sentence splitting
            sentences = NLPService.split_sentences(text)
            logger.info(f"[OpenRouter] Split text into {len(sentences)} sentence(s)")
            
            import asyncio
            # Process sentences in parallel
            tasks = [OpenRouterService._analyze_sentence(s) for s in sentences]
            analyzed_sentences = await asyncio.gather(*tasks)
            
            logger.info(f"[OpenRouter] Analysis complete. Processed {len(analyzed_sentences)} sentences")
            return list(analyzed_sentences)
            
        except Exception as e:
            logger.error(f"[OpenRouter] Error analyzing text with OpenRouter: {str(e)}", exc_info=True)
            raise ProcessingError(f"Failed to analyze text: {str(e)}")
    
    @staticmethod
    async def _analyze_sentence(sentence: str) -> SentenceAnalysis:
        """
        Analyze a single sentence for grammatical components using OpenRouter.
        
        Uses caching to avoid re-analyzing the same sentences.
        
        Args:
            sentence: Sentence to analyze
            
        Returns:
            SentenceAnalysis with extracted components
        """
        from app.cache_service import CacheManager
        
        # Normalize sentence for caching (lowercase, stripped)
        normalized_sentence = sentence.lower().strip()
        cache_key = CacheManager.generate_key("sentence", normalized_sentence)
        
        # Check cache first
        cached_result = CacheManager.get(cache_key)
        if cached_result:
            logger.info(f"[Cache] Hit for sentence: {sentence[:50]}... - returning cached analysis")
            return cached_result
        
        logger.info(f"[OpenRouter] Analyzing sentence: {sentence}")
        prompt = OpenRouterService._build_analysis_prompt(sentence)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"[OpenRouter] Prompt length: {len(prompt)} chars")
        
        client = OpenRouterService.get_client()
        logger.info(f"[OpenRouter] Sending request to {settings.OPENROUTER_BASE_URL} with model: {settings.LLM_MODEL}")
        
        response = await client.post(
            "/chat/completions",
            json={
                "model": settings.LLM_MODEL,
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
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"[OpenRouter] LLM response received ({len(content)} chars)")
        
        # Parse the LLM response
        components, sentence_translation = OpenRouterService._parse_llm_response(content, sentence)
        
        logger.info(f"[OpenRouter] Extracted {len(components)} components from sentence")
        if logger.isEnabledFor(logging.DEBUG):
            for component in components:
                logger.debug(f"  - {component.type}: {component.value}")
        
        # Create the result
        analysis_result = SentenceAnalysis(
            sentence=sentence,
            sentence_translation=sentence_translation,
            components=components
        )
        
        # Cache the result
        CacheManager.set(cache_key, analysis_result)
        logger.info(f"[Cache] Stored analysis for: {sentence[:50]}...")
        
        return analysis_result
    
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
                logger.warning(f"[OpenRouter] Could not find JSON in LLM response")
                return [], None
            
            json_str = content[json_start:json_end]
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"[OpenRouter] Extracted JSON ({len(json_str)} chars)")
            
            response_data = json.loads(json_str)
            
            # Extract sentence translation
            sentence_translation = response_data.get("sentence_translation")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"[OpenRouter] Translation: {sentence_translation}")
            
            # Extract components
            components_data = response_data.get("components", [])
            
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
            
            return components, sentence_translation
            
        except json.JSONDecodeError as e:
            logger.warning(f"[OpenRouter] Failed to parse JSON from LLM response: {e}")
            return [], None
    
    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """
        Split text into sentences using NLPService.
        """
        return NLPService.split_sentences(text)

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
    async def conjugate_dutch_verb(verb: str) -> dict:
        """
        Generate Dutch verb conjugation using OpenRouter LLM.
        
        Generates conjugations for all 6 tenses and 6 persons for a given verb.
        
        Args:
            verb: The infinitive form of the Dutch verb
            
        Returns:
            Dictionary with conjugation data in the standard format
            
        Raises:
            ProcessingError: If LLM call or parsing fails
        """
        if not settings.OPENROUTER_API_KEY:
            raise ProcessingError("OPENROUTER_API_KEY environment variable not set")
        
        try:
            logger.info(f"[OpenRouter] Requesting conjugation for verb: {verb}")
            
            client = OpenRouterService.get_client()
            
            response = await client.post(
                "/chat/completions",
                json={
                    "model": settings.LLM_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert Dutch language teacher. Generate accurate verb conjugations in strict JSON format."
                        },
                        {
                            "role": "user",
                            "content": OpenRouterService._build_conjugation_prompt(verb)
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000,
                },
            )
            
            logger.info(f"[OpenRouter] Conjugation response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"[OpenRouter] API error: {response.status_code} - {response.text}")
                raise ProcessingError(f"OpenRouter API error: {response.status_code}")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse the conjugation response
            conjugation_data = OpenRouterService._parse_conjugation_response(content, verb)
            logger.info(f"[OpenRouter] Successfully generated conjugation for '{verb}'")
            
            return conjugation_data
            
        except Exception as e:
            logger.error(f"[OpenRouter] Failed to conjugate verb '{verb}': {str(e)}")
            raise ProcessingError(f"Failed to conjugate verb '{verb}': {str(e)}")
    
    @staticmethod
    def _build_conjugation_prompt(verb: str) -> str:
        """
        Build the prompt for generating verb conjugations.
        
        Args:
            verb: The infinitive form of the Dutch verb
            
        Returns:
            Prompt string for the LLM
        """
        return f"""Generate a complete Dutch verb conjugation for the infinitive: "{verb}"

Return a JSON object with exactly this structure:
{{
  "infinitive": "{verb}",
  "englishTranslation": "the English translation of the infinitive",
  "verbType": "regular or irregular",
  "tenses": [
    {{
      "dutchName": "Tegenwoordige Tijd",
      "englishName": "Present",
      "forms": [
        {{"person": "ik", "conjugation": "the conjugated form"}},
        {{"person": "je/jij", "conjugation": "the conjugated form"}},
        {{"person": "hij/zij/het", "conjugation": "the conjugated form"}},
        {{"person": "wij", "conjugation": "the conjugated form"}},
        {{"person": "jullie", "conjugation": "the conjugated form"}},
        {{"person": "zij", "conjugation": "the conjugated form"}}
      ]
    }},
    {{
      "dutchName": "Onvoltooid Verleden Tijd",
      "englishName": "Simple Past",
      "forms": [...]
    }},
    {{
      "dutchName": "Voltooid Tegenwoordige Tijd",
      "englishName": "Present Perfect",
      "forms": [...]
    }},
    {{
      "dutchName": "Voltooid Verleden Tijd",
      "englishName": "Past Perfect",
      "forms": [...]
    }},
    {{
      "dutchName": "Toekomende Tijd",
      "englishName": "Future Simple",
      "forms": [...]
    }},
    {{
      "dutchName": "Voorwaardelijke Wijs",
      "englishName": "Conditional",
      "forms": [...]
    }}
  ],
  "examples": [
    {{"dutch": "example sentence in Dutch", "english": "English translation", "tense": "Present"}},
    {{"dutch": "example sentence in Dutch", "english": "English translation", "tense": "Simple Past"}},
    {{"dutch": "example sentence in Dutch", "english": "English translation", "tense": "Present Perfect"}},
    {{"dutch": "example sentence in Dutch", "english": "English translation", "tense": "Future Simple"}}
  ]
}}

Important rules:
1. All 6 persons must be conjugated for each tense
2. Include auxiliary verbs (zijn, hebben) in perfect and past perfect tenses
3. The verbType should be "regular" or "irregular"
4. Provide 4 practical examples with the conjugated verb
5. Return ONLY valid JSON, no other text
6. It must be the correct conjugation for the verb provided, do not conjugate a different verb or make up a verb. If the verb is not recognized, return an error message in the JSON with an "error" field instead of the conjugation data.
7. If the input is not in the infinitive form find the infinitive and use that, if it is not a verb or not recognized return an error message in the JSON with an "error" field instead of the conjugation data.
Ensure the JSON is properly formatted and valid."""

    @staticmethod
    def _parse_conjugation_response(content: str, verb: str) -> dict:
        """
        Parse the LLM conjugation response.
        
        Args:
            content: The LLM response content
            verb: The original verb (for validation)
            
        Returns:
            Dictionary with conjugation data
        """
        try:
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning(f"[OpenRouter] Could not find JSON in conjugation response: {content}")
                raise ProcessingError(f"Invalid response format for verb '{verb}'")
            
            json_str = content[json_start:json_end]
            logger.debug(f"[OpenRouter] Extracted conjugation JSON")
            
            conjugation_data = json.loads(json_str)
            logger.debug(f"[OpenRouter] Parsed conjugation data")
            
            # Validate structure
            required_fields = ['infinitive', 'englishTranslation', 'verbType', 'tenses', 'examples']
            for field in required_fields:
                if field not in conjugation_data:
                    logger.warning(f"[OpenRouter] Missing field in conjugation: {field}")
                    conjugation_data[field] = None if field != 'tenses' else []
            
            # Validate tenses
            if len(conjugation_data.get('tenses', [])) < 6:
                logger.warning(f"[OpenRouter] Insufficient tenses in response: {len(conjugation_data.get('tenses', []))}")
            
            return conjugation_data
            
        except json.JSONDecodeError as e:
            logger.error(f"[OpenRouter] Failed to parse conjugation JSON: {str(e)}")
            raise ProcessingError(f"Failed to parse verb conjugation: {str(e)}")
        except Exception as e:
            logger.error(f"[OpenRouter] Unexpected error parsing conjugation: {str(e)}")
            raise ProcessingError(f"Unexpected error: {str(e)}")
