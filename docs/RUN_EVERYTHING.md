# 🚀 Quick Start - Run Frontend & Backend Together

## Setup (One-Time)

### 1. Backend Setup

```bash
cd /Users/alins/dutchhelper/backend
pip install -r requirements.txt
export OPENROUTER_API_KEY=your_actual_key_here
```

### 2. Frontend Setup

```bash
cd /Users/alins/dutchhelper/frontend
npm install
```

## Running (Daily)

### Terminal 1 - Backend

```bash
cd /Users/alins/dutchhelper/backend
export OPENROUTER_API_KEY=your_actual_key_here
PYTHONPATH=/Users/alins/dutchhelper/backend python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Wait for:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Terminal 2 - Frontend

```bash
cd /Users/alins/dutchhelper/frontend
npm run dev
```

Wait for:

```
  VITE v7.3.1  ready in 344 ms
  ➜  Local:   http://localhost:5173/
```

### Terminal 3 - Open Browser

```
http://localhost:5173/
```

## What to See

### Home Page

- "Welcome to DutchHelper API"
- "Sentence Explainer" link
- API docs link

### Click "Sentence Explainer"

You'll see:

- Header with "✅ Backend Connected" or "❌ Backend Offline"
- Left side: textarea for Dutch text
- Right side: analysis results

### Type Dutch Text

Example:

```
Ik ben een jongen. De kat zit op de mat.
```

### See Results

Left side shows:

- Original text
- Character count

Right side shows:

- Number of sentences found (2)
- Each sentence broken down
- Grammatical components:
  - [subject: 'Ik']
  - [verb: 'ben']
  - [article: 'een']
  - [noun: 'jongen']
  - etc.
- Summary statistics

## Troubleshooting

### "❌ Backend Offline"

1. Check Terminal 1 is running backend
2. Check `http://localhost:8000` in browser
3. Check OPENROUTER_API_KEY is set

### "Empty analysis results"

1. Check backend logs in Terminal 1
2. Check if API key is valid
3. Make sure you have network connection

### "Cannot connect to backend"

1. Check port 8000 is not in use:

   ```bash
   lsof -i :8000
   ```

2. Start backend server again

### "Blank page in frontend"

1. Check Terminal 2 shows no errors
2. Check `http://localhost:5173` loads
3. Open browser console (F12) for JS errors

## ✅ Success Indicators

**Backend Terminal:**

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Frontend Terminal:**

```
  ➜  Local:   http://localhost:5173/
  ➜  press h + enter to show help
```

**Browser:**

- Shows "Sentence Explainer" page
- Header shows "✅ Backend Connected"
- Textarea ready for input
- Results appear as you type

## 🎯 Tips

- Keep both terminals running
- Don't close either terminal
- Check logs if something goes wrong
- Use F12 to check browser console
- Check terminal output for errors

## 📝 Files Used

Backend:

- `backend/app/main.py` - FastAPI app
- `backend/app/routes.py` - `/api/analyze` endpoint
- `backend/app/llm_service.py` - OpenRouter integration

Frontend:

- `frontend/src/views/SentenceExplainer.vue` - Main component
- `frontend/src/router.js` - Routing
- `frontend/src/main.js` - App entry point

## Next Steps

1. ✅ Frontend integrated with backend
2. ✅ Real-time Dutch text analysis working
3. Consider: Add history, export, more features

---

**You're all set!** 🎉 DutchHelper is now fully functional!
