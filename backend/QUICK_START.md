# Quick Start - OpenRouter Backend

## 🚀 Start Backend (3 Easy Steps)

### 1. Set API Key

```bash
export OPENROUTER_API_KEY=your_key_here
```

### 2. Install Dependencies (if needed)

```bash
cd /Users/alins/dutchhelper/backend
pip install -r requirements.txt
```

### 3. Run Server

```bash
cd /Users/alins/dutchhelper/backend
PYTHONPATH=/Users/alins/dutchhelper/backend python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Server will be at: `http://127.0.0.1:8000`

## 🧪 Test Endpoint

Open another terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Ik ben een jongen."}'
```

## 📖 API Docs

Once running, visit:

- **Swagger UI**: <http://127.0.0.1:8000/docs>
- **ReDoc**: <http://127.0.0.1:8000/redoc>

## 📂 Key Files

| File | Purpose |
|------|---------|
| `app/llm_service.py` | OpenRouter LLM integration |
| `app/services.py` | Business logic for text analysis |
| `app/routes.py` | API endpoints |
| `app/models.py` | Pydantic data models |
| `requirements.txt` | Python dependencies |

## ⚙️ How It Works

1. Request comes to `/api/analyze` with Dutch text
2. `SentenceAnalyzerService` calls `OpenRouterService`
3. OpenRouterService:
   - Splits text into sentences
   - Sends each to Mistral 7B via OpenRouter
   - Parses JSON response
   - Extracts grammatical components
4. Response returned with sentence breakdown

## 🐛 Troubleshooting

**Port already in use?**

```bash
lsof -i :8000
# Kill the process or use a different port
```

**API key not recognized?**

```bash
# Verify it's set
echo $OPENROUTER_API_KEY
# Get a new one from https://openrouter.ai
```

**Import errors?**

```bash
# Make sure PYTHONPATH is set correctly
PYTHONPATH=/Users/alins/dutchhelper/backend python -m ...
```

## 💡 Tips

- Use `--reload` flag during development for auto-restart
- Remove `--reload` for production
- Check `/docs` endpoint for interactive API testing
- Logs show detailed error messages for debugging
