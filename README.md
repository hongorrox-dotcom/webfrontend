# Vensim → Python (PySD) Web Project (FastAPI + React/Vite)

Энэ төсөл нь Vensim `.mdl` моделийг PySD ашиглан ажиллуулж,
Анхны (суурь) ба Симуляци (шинэ) үр дүнг 2x2 графикаар overlay байдлаар харуулна.
Модель уншигдахгүй/алдаатай үед DEMO MODE дээр автоматаар ажиллаж UI тасрахгүй.

## 1) Шаардлага
- Python 3.11 (Windows дээр 3.11 ашиглах)
- Node.js 18+ (эсвэл 20+)
- VS Code

## 2) Backend ажиллуулах (FastAPI)
### 2.1 venv үүсгэх
Windows (PowerShell):
```powershell
cd backend
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

## 3) Quick run (6–10 мөр)
1) backend/.env-д GEMINI_API_KEY оруул (chatbot ажиллахад шаардлагатай).
2) Backend: cd backend → .\venv\Scripts\Activate.ps1 → uvicorn app.main:app --reload --port 8000
3) Frontend: cd frontend → npm install → npm run dev
4) http://localhost:5173/ нээнэ.
5) Симуляци хийгээд график дээр дарж идэвхтэй үзүүлэлтээ сонгоно.
6) Чатбот хэсэгт асуулт бичээд Илгээх дарна.
7) 2035 зэрэг он асуухад time дотор байхгүй бол “өгөгдөл алга” гэж хариулна.
