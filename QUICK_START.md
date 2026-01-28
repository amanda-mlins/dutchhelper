# Quick Start Guide

## Getting Started with DutchHelper

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

---

## Running the Application

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Start the development server
python run.py
```

Backend will be available at: **http://localhost:8000**

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

Frontend will be available at: **http://localhost:5173**

---

## Project Structure

### Backend (`/backend`)
```
app/
├── main.py          # FastAPI app + logging
├── routes.py        # API endpoints
├── models.py        # Pydantic schemas
├── services.py      # Business logic
├── exceptions.py    # Error handling
└── __init__.py
```

### Frontend (`/frontend`)
```
src/
├── App.vue          # (deprecated - use AppMain.vue)
├── AppMain.vue      # Root component with router
├── router.js        # Vue Router configuration
├── main.js          # Application entry point
├── style.css        # Global styles
├── views/
│   ├── Home.vue            # Index page
│   └── SentenceExplainer.vue  # Analysis tool
├── components/      # (future)
└── public/          # Static files
```

---

## API Endpoints

### Health & Info
```bash
GET /
GET /health
```

### Text Analysis (Main Feature)
```bash
POST /api/analyze
Content-Type: application/json

{
  "text": "Dit is een Nederlands zin."
}
```

**Response:**
```json
{
  "original_text": "Dit is een Nederlands zin.",
  "sentences": [
    {
      "sentence": "Dit is een Nederlands zin.",
      "components": []
    }
  ],
  "summary": null
}
```

### Testing Endpoint
```bash
POST /api/message
Content-Type: application/json

{
  "text": "Hello"
}
```

---

## Frontend Navigation

### Home Page (`/`)
- Welcome message
- Tools grid with available features
- Navigation to Sentence Explainer

### Sentence Explainer (`/sentence-explainer`)
- Dutch text input area
- Real-time grammatical analysis
- Display of identified components
- Character counter and statistics

---

## Development Commands

### Backend
```bash
# Run development server
python run.py

# Run with specific port
API_PORT=8001 python run.py

# Enable debug mode
DEBUG=true python run.py
```

### Frontend
```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## Key Files & Where to Modify

### To Add New Features
1. **New API Endpoint?** → Edit `/backend/app/routes.py`
2. **Business Logic?** → Edit `/backend/app/services.py`
3. **New Data Model?** → Edit `/backend/app/models.py`
4. **New Page?** → Create in `/frontend/src/views/`
5. **Update Navigation?** → Edit `/frontend/src/router.js`

### To Integrate NLP
1. Install spaCy: `pip install spacy`
2. Download Dutch model: `python -m spacy download nl_core_news_sm`
3. Update `SentenceAnalyzerService._analyze_sentence()` in `/backend/app/services.py`
4. Frontend will automatically display results!

---

## Environment Variables

### Backend (`.env` in `/backend`)
```
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

### Frontend
No env file needed, but API base URL is set in:
- `/frontend/src/views/SentenceExplainer.vue` (line ~143)
- Default: `http://localhost:8000`

---

## Common Issues & Solutions

### CORS Errors
**Problem:** Frontend can't reach backend
**Solution:** Ensure backend is running and CORS is configured
- Check `app/main.py` for CORS middleware
- Verify frontend URL is in `allow_origins`

### Port Already in Use
**Backend:**
```bash
API_PORT=8001 python run.py
```

**Frontend:**
```bash
npm run dev -- --port 5174
```

### Module Not Found
**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

---

## Testing the Integration

### Using curl/Postman

1. **Test backend health:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Test analyze endpoint:**
   ```bash
   curl -X POST http://localhost:8000/api/analyze \
     -H "Content-Type: application/json" \
     -d '{"text": "Dit is een test."}'
   ```

3. **View API documentation:**
   Open http://localhost:8000/docs in browser

### Using Frontend
1. Open http://localhost:5173
2. Click "Sentence Explainer"
3. Type Dutch text in the input area
4. See analysis appear in real-time

---

## Project Status

✅ **Backend** - Production-ready
✅ **Frontend** - Production-ready
✅ **Integration** - Complete
⏳ **NLP Analysis** - Ready for implementation

---

## Next Steps

1. **Test the Application**
   - Run both backend and frontend
   - Navigate through pages
   - Test the analyze endpoint

2. **Implement NLP**
   - Add spaCy integration
   - Implement grammatical analysis
   - Test with Dutch sentences

3. **Customize Styling**
   - Adjust colors in CSS
   - Modify component layouts
   - Add new features

4. **Deploy**
   - Set up production environment
   - Configure environment variables
   - Deploy to hosting platform

---

## Documentation Files

- `REFACTORING_SUMMARY.md` - Complete overview of changes
- `BACKEND_STRUCTURE.md` - Detailed backend analysis
- `BACKEND_BEFORE_AFTER.md` - Before/after code comparison
- `IMPLEMENTATION_CHECKLIST.md` - Verification checklist
- `QUICK_START.md` - This file!

---

## Getting Help

1. Check the documentation files
2. Review inline code comments
3. Check FastAPI docs: https://fastapi.tiangolo.com/
4. Check Vue 3 docs: https://vuejs.org/
5. Check spaCy docs for NLP: https://spacy.io/

---

## Support

For questions or issues:
1. Review the code structure
2. Check error logs (backend console)
3. Check browser console (frontend)
4. Refer to documentation

---

Good luck! 🚀 Your DutchHelper app is ready to go!
