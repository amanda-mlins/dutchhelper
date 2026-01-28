# OpenRouter Integration Setup Guide

## Overview

Your DutchHelper backend is now integrated with OpenRouter's Mistral 7B model to analyze Dutch text and extract grammatical components.

## Files Created/Modified

### 1. **New Files**

- `app/llm_service.py` - OpenRouter LLM service for Dutch text analysis

### 2. **Modified Files**

- `app/services.py` - Updated to use OpenRouter LLM instead of placeholder logic
- `app/routes.py` - Made `/api/analyze` endpoint async
- `requirements.txt` - Added `httpx==0.25.2` for async HTTP requests
- `.env.example` - Added `OPENROUTER_API_KEY` configuration

## Setup Instructions

### Step 1: Set Your OpenRouter API Key

Make sure you have set the `OPENROUTER_API_KEY` environment variable:

```bash
export OPENROUTER_API_KEY=your_actual_api_key_here
```

Or add it to a `.env` file in the backend directory:

```
OPENROUTER_API_KEY=your_actual_api_key_here
```

### Step 2: Install Dependencies (Already Done)

```bash
cd /Users/alins/dutchhelper/backend
pip install -r requirements.txt
```

### Step 3: Start the Backend Server

```bash
cd /Users/alins/dutchhelper/backend
PYTHONPATH=/Users/alins/dutchhelper/backend python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 4: Test the Endpoint

In another terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Ik ben een jongen."}'
```

Expected response:

```json
{
  "original_text": "Ik ben een jongen.",
  "sentences": [
    {
      "sentence": "Ik ben een jongen.",
      "components": [
        {
          "type": "subject",
          "value": "Ik",
          "position": 0
        },
        {
          "type": "verb",
          "value": "ben",
          "position": 3
        },
        // ... more components
      ]
    }
  ]
}
```

## How It Works

1. **Frontend sends text** → `/api/analyze` endpoint
2. **Backend processes request** → Calls `OpenRouterService.analyze_dutch_text()`
3. **OpenRouterService**:
   - Splits text into sentences
   - For each sentence, sends a prompt to Mistral 7B on OpenRouter
   - Parses the LLM response (JSON format)
   - Returns structured `SentenceAnalysis` objects
4. **Response returned** with grammatical components

## Cost Estimates

- **Model**: Mistral 7B (free on OpenRouter)
- **Volume**: 200 requests/day
- **Text size**: ~200 characters (~40 tokens per request)
- **Monthly cost**: ~$0.04 (practically free!)

## Architecture

```
Vue Frontend (localhost:5173)
           ↓
    /api/analyze (POST)
           ↓
FastAPI Backend (app/routes.py)
           ↓
SentenceAnalyzerService
           ↓
OpenRouterService (app/llm_service.py)
           ↓
OpenRouter API (https://openrouter.ai)
           ↓
Mistral 7B LLM
           ↓
JSON Response with grammatical analysis
           ↓
Frontend displays results
```

## Troubleshooting

### ModuleNotFoundError: No module named 'app'

Make sure you're running from the backend directory with correct PYTHONPATH:

```bash
cd /Users/alins/dutchhelper/backend
PYTHONPATH=/Users/alins/dutchhelper/backend python -m uvicorn app.main:app --reload
```

### ProcessingError: OPENROUTER_API_KEY environment variable not set

Ensure your API key is set:

```bash
echo $OPENROUTER_API_KEY  # Should show your key
```

If not set, add it to `.env`:

```
OPENROUTER_API_KEY=your_key_here
```

### No response from OpenRouter

Check:

1. Your API key is valid at <https://openrouter.ai>
2. You have sufficient credits
3. The OpenRouter API is accessible from your network
4. Check logs for detailed error messages

## Next Steps

1. ✅ OpenRouter integration complete
2. Test with the frontend
3. Refine prompts if needed for better accuracy
4. Add caching to reduce API calls (optional)
5. Add rate limiting for production (optional)
