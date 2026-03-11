# DutchHelper

A full-stack Dutch language learning app with interactive games, AI-powered analysis, spaced repetition, a personal word bank, and more.

**Built with:** FastAPI (Python) + Vue.js 3 + SQLite

---

## 🌐 Live Demo

**[https://unique-figolla-d56503.netlify.app/](https://unique-figolla-d56503.netlify.app/)**

---

## Features

### 🎮 Language Games

- **Article Game** — Practice *de* vs *het* with difficulty levels and spaced repetition
- **Verb Conjugation Game** — Fill in the correct conjugated verb form across tenses
- **Conjunction Game** — Choose the right coordinating, subordinating or correlative conjunction
- **Prep-Verb Game** — Master fixed preposition combinations (*beginnen **met****, *denken **aan****, *houden **van***)

### 📖 Learning Tools

- **Sentence Explainer** — AI-powered grammatical breakdown of any Dutch sentence (subject, verb, object, articles, etc.)
- **Word Conjugator** — Look up full conjugation tables for any Dutch verb
- **Word Bank** — Save vocabulary with translations, categories and example sentences; export to CSV/Anki
- **Flashcards** — Review saved words with multiple study modes (definition, fill-in, multiple choice)

### 🔁 Spaced Repetition

All games track per-user performance and surface words/pairs that need review, prioritising items with high error rates.

### 🔒 Authentication

- Email/password registration + login
- OAuth (Google / GitHub) via social login
- JWT-based session management

### 🛠️ Admin Panel

- Article word cache management
- Verb conjugation cache with re-fetch from LLM
- Conjunction sentence cache (view, edit, delete)
- Prep-verb pair cache (edit sentences for both game modes)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy, SQLite |
| AI | OpenRouter (LLM calls for sentence generation & analysis) |
| Frontend | Vue 3, Vue Router 4, Vite, Axios |
| Auth | JWT, OAuth2 (Google/GitHub) |
| Hosting | Netlify (frontend), self-hosted backend |

---

## Project Structure

```
dutchhelper/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app init, CORS, logging
│   │   ├── routes.py                # All API endpoints
│   │   ├── models.py                # SQLAlchemy ORM models
│   │   ├── schemas.py               # Pydantic request/response schemas
│   │   ├── services.py              # Core business logic
│   │   ├── llm_service.py           # OpenRouter / LLM integration
│   │   ├── prep_verb_game_service.py# Fixed-preposition verb game logic
│   │   └── exceptions.py            # Custom error handling
│   ├── requirements.txt
│   └── run.py
└── frontend/
    ├── src/
    │   ├── main.js
    │   ├── router.js
    │   ├── AppMain.vue
    │   ├── stores/
    │   │   └── auth.js              # Pinia auth store
    │   ├── components/
    │   │   ├── Navbar.vue
    │   │   └── WordBankButton.vue   # One-click word saving
    │   └── views/
    │       ├── Home.vue
    │       ├── SentenceExplainer.vue
    │       ├── Conjugator.vue
    │       ├── ArticleGame.vue / ArticleGameStats.vue
    │       ├── VerbGame.vue / VerbGameStats.vue
    │       ├── ConjunctionGame.vue / ConjunctionGameStats.vue
    │       ├── PrepVerbGame.vue
    │       ├── WordBank.vue
    │       ├── Flashcards.vue
    │       ├── Profile.vue
    │       ├── Login.vue / Register.vue
    │       └── Admin*.vue           # Admin pages
    ├── package.json
    └── vite.config.js
```

---

## Local Development

### Prerequisites

- Python 3.10+
- Node.js 18+
- An [OpenRouter](https://openrouter.ai/) API key (for AI features)

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # add your OPENROUTER_API_KEY
python run.py
```

API runs at `http://localhost:8000`  
Swagger docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

### Production Build

```bash
cd frontend
npm run build
# Static files output to frontend/dist/
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | Required for all AI/LLM features |
| `SECRET_KEY` | JWT signing secret |
| `DATABASE_URL` | SQLite path (default: `./dutchhelper.db`) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | OAuth — Google |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | OAuth — GitHub |
| `FRONTEND_URL` | Allowed CORS origin |

---

## API Overview

```
GET  /health                          Health check

# Auth
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me

# Games
POST /api/article-game/question
POST /api/verb-game/question
POST /api/conjunction-game/question
POST /api/prep-verb-game/question
POST /api/*/save                      Save completed game session
GET  /api/*/stats                     Per-user game statistics

# Tools
POST /api/analyze                     Sentence grammatical analysis
GET  /api/conjugate/{verb}            Verb conjugation table

# Word Bank
GET  /api/word-bank/words
POST /api/word-bank/words
POST /api/word-bank/words/quick       Fast add (no LLM)
DELETE /api/word-bank/words/{id}

# Admin (is_admin required)
GET/PATCH/DELETE /api/admin/words/{id}
GET/PATCH/DELETE /api/admin/verbs/{id}
GET/PATCH/DELETE /api/admin/conjunction-sentences/{id}
GET/PATCH/DELETE /api/admin/prep-verb-pairs/{id}
```

---

## License

MIT — see [LICENSE](LICENSE).
