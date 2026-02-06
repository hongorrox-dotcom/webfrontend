Backend (FastAPI) ажиллуулах

1) Python virtual env (Python 3.11)
- Windows (PowerShell):
  py -3.11 -m venv venv
  .\venv\Scripts\Activate.ps1
- macOS/Linux:
  python3.11 -m venv venv
  source venv/bin/activate

2) Dependency суулгах
  pip install -r requirements.txt

3) .env үүсгэх
  backend/.env.example-г хуулж backend/.env болгоод:
  - MODEL_PATH (сонголттой)
  - GEMINI_API_KEY (AI тайлбар ашиглах бол шаардлагатай)

4) Run
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

API:
- GET  http://localhost:8000/api/state
- POST http://localhost:8000/api/run
- POST http://localhost:8000/api/explain
