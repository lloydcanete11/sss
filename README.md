# 🏸 ShuttlePro — Badminton Shop

Full-stack badminton e-commerce app.

## Tech Stack
| Layer      | Technology                      |
|------------|---------------------------------|
| Frontend   | HTML5 + CSS3 + Vanilla JS       |
| Backend    | Python 3 + Flask (REST API)     |
| Database   | SQLite (via Python `sqlite3`)   |

## Project Structure
```
shuttlepro/
├── app.py              ← Flask backend (all API routes)
├── requirements.txt    ← Python dependencies
├── shuttlepro.db       ← SQLite database (auto-created)
└── static/
    └── index.html      ← Frontend (HTML + CSS + JS)
```

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the backend
```bash
python app.py
```
Server starts at **http://localhost:5000**

### 3. Open the shop
Visit **http://localhost:5000** in your browser.

---

## API Endpoints

| Method | Endpoint                          | Description              |
|--------|-----------------------------------|--------------------------|
| GET    | /api/products                     | All products             |
| GET    | /api/products?category=racket     | Filter by category       |
| GET    | /api/products/search?q=yonex      | Search products          |
| GET    | /api/products/:id                 | Single product           |
| GET    | /api/cart/:session_id             | Get cart                 |
| POST   | /api/cart/:session_id/add         | Add item to cart         |
| DELETE | /api/cart/:session_id/remove/:id  | Remove cart item         |
| DELETE | /api/cart/:session_id/clear       | Clear cart               |
| POST   | /api/auth/register                | Register user            |
| POST   | /api/auth/login                   | Login                    |
| POST   | /api/orders                       | Place order              |
| GET    | /api/orders/:email                | Get user orders          |
| POST   | /api/newsletter                   | Subscribe                |
| GET    | /api/stats                        | Site statistics          |

---

> **Offline mode**: The frontend automatically falls back to demo data if the backend is not running.
