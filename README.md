# Quant System

Personal quantitative strategy system workspace.

Current status:

- VeighNa/vn.py desktop entry is available through `run_veighna.py`.
- Product requirements and architecture are documented in `docs/quant-system-prd-and-architecture.md`.
- The planned Web system uses a FastAPI backend plus two React/Vite frontends: one admin frontend and one client display frontend.

## Local Setup

Use Python 3.13 on Windows.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Start VeighNa Desktop

```powershell
.\.venv\Scripts\python.exe run_veighna.py
```

## Documents

- `docs/quant-system-prd-and-architecture.md`: approved V1 PRD and architecture direction.
