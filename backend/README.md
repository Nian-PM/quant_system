# Quant System Backend

FastAPI backend for the personal quant system.

## Run

```powershell
cd E:\Project\quant
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

Health check:

```text
http://127.0.0.1:8000/api/health
```
