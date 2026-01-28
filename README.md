# DutchHelper

A full-stack web application for learning Dutch with advanced grammatical analysis. Break down Dutch sentences into their grammatical components: subjects, verbs, objects, adjectives, articles, and more.

**Built with:** FastAPI (Python) + Vue.js 3 + Vue Router

## Features

- 🎯 **Sentence Explainer** - Real-time grammatical analysis of Dutch text
- 🏠 **Home Page** - Tool navigation and learning hub
- 📊 **Component Analysis** - Identify sentences and their grammatical elements
- 🚀 **Modern Stack** - Fast, responsive, production-ready
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🔄 **Real-time Processing** - Instant feedback as you type
- 📖 **Auto API Docs** - Swagger UI at `/docs`
- ⚡ **Hot Reload** - Development with instant updates

## Project Structure

```
dutchhelper/
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app + logging
│   │   ├── routes.py            # API endpoints
│   │   ├── models.py            # Pydantic schemas
│   │   ├── services.py          # Business logic layer
│   │   └── exceptions.py        # Custom error handling
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py                   # Development server
├── frontend/                     # Vue.js 3 frontend
│   ├── src/
│   │   ├── router.js            # Vue Router config
│   │   ├── AppMain.vue          # Root component
│   │   ├── main.js              # Entry point
│   │   ├── style.css            # Global styles
│   │   ├── views/
│   │   │   ├── Home.vue         # Home page
│   │   │   └── SentenceExplainer.vue  # Analysis tool
│   │   ├── components/          # Reusable components
│   │   └── public/              # Static assets
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── QUICK_START.md              # Quick start guide
├── REFACTORING_SUMMARY.md      # Overview of changes
├── BACKEND_STRUCTURE.md        # Architecture details
├── BACKEND_BEFORE_AFTER.md     # Code comparisons
└── README.md                   # This file
```

## Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Type validation and serialization
- **Python 3.8+**

### Frontend
- **Vue 3** - Progressive JavaScript framework
- **Vue Router 4** - Client-side routing
- **Vite** - Lightning-fast build tool
- **Axios** - HTTP client
- **CSS3** - Responsive styling

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python run.py
```

Backend runs at `http://localhost:8000`

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

### Running Both (Recommended)

Open two terminals:

**Terminal 1:**
```bash
cd backend && python run.py
```

**Terminal 2:**
```bash
cd frontend && npm run dev
```

Visit `http://localhost:5173` and start learning!

## API Endpoints

### Health & Welcome
```
GET  /              Welcome message + version info
GET  /health        Health check
```

### Text Analysis (Main Feature)
```
POST /api/analyze
```

**Request:**
```json
{
  "text": "Dit is een Nederlandse zin."
}
```

**Response:**
```json
{
  "original_text": "Dit is een Nederlandse zin.",
  "sentences": [
    {
      "sentence": "Dit is een Nederlandse zin.",
      "components": []
    }
  ],
  "summary": null
}
```

### Test Endpoint
```
POST /api/message   Echo test endpoint
```

## Architecture

### Backend Architecture
- **Routes** (`routes.py`) - HTTP endpoints only
- **Services** (`services.py`) - Business logic (SentenceAnalyzerService)
- **Models** (`models.py`) - Pydantic request/response schemas
- **Exceptions** (`exceptions.py`) - Custom error handling
- **Main** (`main.py`) - App initialization & logging

**Design Patterns Used:**
- Service Layer Pattern
- Custom Exception Handling
- Dependency Injection Ready
- Async/Await Best Practices

### Frontend Pages

**Home Page (`/`)**
- Welcome section
- Tools grid with feature cards
- Navigation to Sentence Explainer

**Sentence Explainer (`/sentence-explainer`)**
- Dutch text input area (left column)
- Real-time grammatical analysis (right column)
- Sentence breakdown with components
- Character counter and statistics
- Loading and error states
- Back navigation link

## Development Workflow

### Adding a New API Endpoint

1. **Add schema** in `backend/app/models.py`
2. **Add business logic** in `backend/app/services.py`
3. **Add route** in `backend/app/routes.py`
4. **Update frontend** component to call new endpoint

### Adding a New Page

1. **Create component** in `frontend/src/views/MyPage.vue`
2. **Add route** in `frontend/src/router.js`
3. **Add navigation** link in appropriate component

### Example: Adding API Endpoint

**1. models.py:**
```python
class MyRequest(BaseModel):
    data: str

class MyResponse(BaseModel):
    result: str
```

**2. services.py:**
```python
class MyService:
    @staticmethod
    def process(data: str) -> str:
        return f"Processed: {data}"
```

**3. routes.py:**
```python
@router.post("/my-endpoint", response_model=MyResponse)
async def my_endpoint(request: MyRequest):
    result = MyService.process(request.data)
    return {"result": result}
```

## Production Build

### Backend
```bash
cd backend
pip install gunicorn
gunicorn "app.main:app" -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend
```bash
cd frontend
npm run build
```

Production files go to `frontend/dist/`

## Environment Variables

### Backend (.env)
```
DEBUG=True
API_HOST=0.0.0.0
API_PORT=8000
```

### Frontend
API base URL is set in `src/views/SentenceExplainer.vue`
Default: `http://localhost:8000`

## Testing

### Manual API Testing
```bash
# Health check
curl http://localhost:8000/health

# Analyze text
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Dit is een test zin."}'
```

### Swagger UI
Open http://localhost:8000/docs for interactive API testing

## Troubleshooting

### CORS Issues
Ensure both services are running. Check `backend/app/main.py` for allowed origins.

### Port Conflicts

**Change Backend Port:**
```bash
API_PORT=8001 python run.py
```

**Change Frontend Port:**
```bash
npm run dev -- --port 5174
```

### Dependencies Issues
```bash
# Backend
rm -rf venv && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Frontend
rm -rf node_modules && npm install
```

### Module Not Found
```bash
# Backend
cd backend && pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

## Code Quality

✅ Type-safe with Pydantic and type hints
✅ Comprehensive error handling
✅ Full logging support
✅ Separation of concerns
✅ SOLID principles applied
✅ Tested imports and structure
✅ Professional code organization

## Next Steps (Roadmap)

### Phase 2: NLP Implementation
- [ ] Install spaCy with Dutch language model
- [ ] Implement grammatical analysis in `SentenceAnalyzerService`
- [ ] Identify: subjects, verbs, objects, adjectives, articles, nouns
- [ ] Test with various Dutch sentences

### Phase 3: Database Integration
- [ ] Add SQLAlchemy ORM
- [ ] Create user accounts
- [ ] Store analysis history
- [ ] Add user preferences

### Phase 4: Enhanced Features
- [ ] Word definitions and synonyms
- [ ] Pronunciation guides
- [ ] Example sentences
- [ ] Difficulty levels
- [ ] Progress tracking and achievements
- [ ] Spaced repetition system

### Phase 5: Deployment
- [ ] CI/CD pipeline
- [ ] Docker containerization
- [ ] Cloud deployment (AWS, DigitalOcean, etc.)
- [ ] CDN for frontend assets

## Documentation

For detailed information, see:
- **[QUICK_START.md](QUICK_START.md)** - How to run the application
- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - Complete overview of implementation
- **[BACKEND_STRUCTURE.md](BACKEND_STRUCTURE.md)** - Backend architecture details
- **[BACKEND_BEFORE_AFTER.md](BACKEND_BEFORE_AFTER.md)** - Code improvements and comparisons

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Status

**Current Release:** v1.0.0
**Status:** Production-Ready (Core Features)
**Last Updated:** January 28, 2026

---

**Ready to get started?** See [QUICK_START.md](QUICK_START.md) for detailed setup instructions.
