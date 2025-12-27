# Home Network Management System (HNMS)

A web-based home network management system for scanning devices, tracking history, and managing network configuration.

## Tech Stack
- **Backend:** FastAPI, DuckDB
- **Frontend:** Vue 3, Vite, Tailwind CSS

---

## Backend Setup

### 1. Install Dependencies
Ensure you have Python installed. Run the following in the `backend` directory:
```bash
pip install -r requirements.txt
```

### 2. Run the App
Start the FastAPI server:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```
The backend will be available at [http://localhost:8001](http://localhost:8001).

---

## Frontend Setup

### 1. Install Dependencies
Ensure you have Node.js installed. Run the following in the `ui` directory:
```bash
npm install
```

### 2. Run the App
Start the Vite development server:
```bash
npm run dev
```
The frontend will be available at [http://localhost:5173](http://localhost:5173).

---

## Project Structure
- `/backend`: FastAPI application and DuckDB database.
- `/ui`: Vue 3 frontend application.
- `/data`: Database storage location.