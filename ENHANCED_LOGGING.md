# Enhanced Logging for OpenRouter Model Calls

## ✨ What's New

Your backend now has comprehensive logging for all OpenRouter model calls. Every step of the analysis is logged with helpful context.

## 🎯 Quick Start to See Logs

### Terminal 1: Start Server

```bash
cd /Users/alins/dutchhelper/backend
PYTHONPATH=/Users/alins/dutchhelper/backend python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

You'll see the Uvicorn banner, then it waits for requests.

### Terminal 2: Make a Request

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Ik ben een jongen. De kat zit."}'
```

### Terminal 1: Watch the Logs

You'll see something like:

```
2026-01-28 10:35:20,123 - app.routes - INFO - Analyzing text: Ik ben een jongen. De kat zit....
2026-01-28 10:35:20,124 - app.llm_service - INFO - [OpenRouter] Starting analysis of text: Ik ben een jongen. De kat zit....
2026-01-28 10:35:20,124 - app.llm_service - INFO - [OpenRouter] Split text into 2 sentence(s)
2026-01-28 10:35:20,124 - app.llm_service - INFO - [OpenRouter] Processing sentence 1/2
2026-01-28 10:35:20,125 - app.llm_service - INFO - [OpenRouter] Analyzing sentence: Ik ben een jongen.
2026-01-28 10:35:20,125 - app.llm_service - INFO - [OpenRouter] Sending request to https://openrouter.ai/api/v1/chat/completions with model: mistralai/mistral-small-3.1-24b-instruct:free
2026-01-28 10:35:22,345 - app.llm_service - INFO - [OpenRouter] Response status: 200
2026-01-28 10:35:22,345 - app.llm_service - INFO - [OpenRouter] Extracted 4 components from sentence
2026-01-28 10:35:22,345 - app.llm_service - DEBUG -   [1] subject: 'Ik'
2026-01-28 10:35:22,345 - app.llm_service - DEBUG -   [2] verb: 'ben'
2026-01-28 10:35:22,345 - app.llm_service - DEBUG -   [3] article: 'een'
2026-01-28 10:35:22,345 - app.llm_service - DEBUG -   [4] noun: 'jongen'
2026-01-28 10:35:22,346 - app.llm_service - INFO - [OpenRouter] Processing sentence 2/2
2026-01-28 10:35:22,346 - app.llm_service - INFO - [OpenRouter] Analyzing sentence: De kat zit.
2026-01-28 10:35:22,347 - app.llm_service - INFO - [OpenRouter] Sending request to https://openrouter.ai/api/v1/chat/completions with model: mistralai/mistral-small-3.1-24b-instruct:free
2026-01-28 10:35:24,567 - app.llm_service - INFO - [OpenRouter] Response status: 200
2026-01-28 10:35:24,567 - app.llm_service - INFO - [OpenRouter] Extracted 3 components from sentence
2026-01-28 10:35:24,567 - app.llm_service - DEBUG -   [1] article: 'De'
2026-01-28 10:35:24,567 - app.llm_service - DEBUG -   [2] noun: 'kat'
2026-01-28 10:35:24,567 - app.llm_service - DEBUG -   [3] verb: 'zit'
2026-01-28 10:35:24,568 - app.llm_service - INFO - [OpenRouter] Analysis complete. Processed 2 sentences
2026-01-28 10:35:24,568 - app.routes - INFO - Analysis complete: 2 sentences found
```

## 📝 Log Messages Explained

### Analysis Start

```
[OpenRouter] Starting analysis of text: Ik ben een jongen....
[OpenRouter] Split text into 2 sentence(s)
```

→ Server received text, split into 2 sentences

### Per-Sentence Processing

```
[OpenRouter] Processing sentence 1/2
[OpenRouter] Analyzing sentence: Ik ben een jongen.
[OpenRouter] Sending request to https://openrouter.ai/api/v1/chat/completions with model: mistralai/mistral-small-3.1-24b-instruct:free
```

→ Processing sentence 1 of 2, about to call the API

### API Response

```
[OpenRouter] Response status: 200
[OpenRouter] Extracted 4 components from sentence
```

→ API call succeeded, got 4 grammatical components

### Components Details

```
  [1] subject: 'Ik'
  [2] verb: 'ben'
  [3] article: 'een'
  [4] noun: 'jongen'
```

→ Shows each extracted grammatical component

## 🔍 Enhanced Logging Details

### What's Logged

✅ **Starting Analysis**

- Original text (first 100 chars)
- Number of sentences created

✅ **Per Sentence**

- Sentence number and total count
- Exact sentence being analyzed
- API endpoint and model being used
- HTTP response status

✅ **Parsing**

- Number of components extracted
- Each component's type and value
- Any parsing errors with details

✅ **Completion**

- Total sentences processed
- Any exceptions with full stack trace

### Log Levels

- **INFO**: Key steps (default - always shown)
  - Analysis start/end
  - API requests/responses
  - Components extracted
  
- **DEBUG**: Detailed information (use `--log-level debug`)
  - Full prompts sent to LLM
  - Full LLM responses
  - Extracted JSON
  - Individual component parsing

- **ERROR**: Failures
  - API errors (with status codes)
  - Parsing failures
  - Connection issues

## 🎛️ Control Logging

### Standard (INFO level only)

```bash
PYTHONPATH=/Users/alins/dutchhelper/backend python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### With DEBUG logs

```bash
PYTHONPATH=/Users/alins/dutchhelper/backend python -m uvicorn app.main:app --log-level debug --reload --host 127.0.0.1 --port 8000
```

### Save logs to file

```bash
PYTHONPATH=/Users/alins/dutchhelper/backend python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 > app.log 2>&1 &
tail -f app.log  # In another terminal
```

### Filter for OpenRouter logs only

```bash
tail -f app.log | grep "\[OpenRouter\]"
```

## 🐛 Troubleshooting with Logs

### Check if API is being called

Look for:

```
[OpenRouter] Sending request to https://openrouter.ai/api/v1/chat/completions
```

### Check API response

Look for:

```
[OpenRouter] Response status: 200
```

- 200 = Success
- 401 = Invalid API key
- 429 = Rate limited
- 500 = Server error

### Check if parsing succeeded

Look for:

```
[OpenRouter] Extracted X components from sentence
```

Each line under this shows a component.

### Check for errors

Look for:

```
ERROR - [OpenRouter]
```

These lines show what went wrong.

## 📂 Files Modified

| File | Change |
|------|--------|
| `app/llm_service.py` | Added comprehensive logging to all methods |
| `LOGGING_GUIDE.md` | Detailed logging documentation |
| `LOGS_QUICK_REFERENCE.md` | Quick reference card |

## 🎓 Example Session

**Input:**

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Ik hou van katten."}'
```

**What You'll See:**

- Request received
- Text split into 1 sentence
- Sentence sent to Mistral 7B
- API response received (status 200)
- 4 components extracted (subject, verb, preposition, object)
- Analysis complete

**You can track the entire flow in the logs!**

## ✨ Summary

- 🟢 All OpenRouter calls are logged
- 🟢 Logs show in real-time in the terminal
- 🟢 Easy to troubleshoot with detailed messages
- 🟢 Use DEBUG level for full request/response details
- 🟢 All model logs prefixed with `[OpenRouter]` for easy filtering
