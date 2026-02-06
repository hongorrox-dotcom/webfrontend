# Deployment Guide

## Python Version Requirements

**Required Python Version: 3.10 - 3.12** (Recommended: 3.12.0)

⚠️ **Note:** Python 3.14 may have compatibility issues with some dependencies like `httpcore`.

### Recommended Setup

```bash
# Check Python version
python --version
# Should output: Python 3.10.x, 3.11.x, or 3.12.x

# Create virtual environment with specific Python version
python3.12 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

## Backend Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file with:

```env
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini
MODEL_PATH=./models/dornodjinkencopy2.mdl
DEMO_MODE_AUTO=1

ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ALLOWED_ORIGIN_REGEX=^http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+):5173$
```

### 3. Run Backend Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Run Frontend Server

```bash
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## Production Deployment

### Python Version for Production

- **Recommended:** Python 3.12.x (LTS stability)
- **Minimum:** Python 3.10.x
- **Avoid:** Python 3.14.x (dependency compatibility issues)

### Environment Variables

Set these in your production environment:

```
OPENAI_API_KEY=your_production_key
OPENAI_MODEL=gpt-4o-mini
MODEL_PATH=./models/dornodjinkencopy2.mdl
DEMO_MODE_AUTO=0 (disable demo mode in production)
ALLOWED_ORIGINS=your_production_domain
ALLOWED_ORIGIN_REGEX=your_production_regex
```

### Docker Deployment Example

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Issue: `AttributeError: 'typing.Union' object has no attribute '__module__'`

**Solution:** This occurs with Python 3.14 and httpcore compatibility. Downgrade to Python 3.12:

```bash
# Remove old venv
rm -rf .venv

# Create new venv with Python 3.12
python3.12 -m venv .venv
source .venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

### Issue: CORS errors

**Solution:** Update `ALLOWED_ORIGINS` in `.env` to match your frontend URL

## Quick Start

```bash
# Clone and setup
git clone https://github.com/hongorrox-dotcom/webfrontend.git
cd webfrontend

# Create venv (Python 3.12 recommended)
python3.12 -m venv .venv
source .venv/bin/activate

# Setup Backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000 &

# Setup Frontend (new terminal)
cd frontend
npm install
npm run dev

# Access application at http://localhost:5173
```

---

**Last Updated:** February 6, 2026
**Tested with:** Python 3.12.0, Node.js 20.x
