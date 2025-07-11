# Tribal Dances of India - Mini Project

This is a mini project showcasing the cultural richness of India's tribal dances using a web portal.

## 🖥️ Features
- Interactive interface with images and information about various tribal dances
- SQLite database for user data (`users.db`)
- Python Flask-based backend (`app.py`)
- Static content served from `static/` folder
- Metadata managed via `metadata.py`

## 🚀 Tech Stack
- Python 3
- Flask
- SQLite
- HTML/CSS + JS (inside `templates` and `static`)
- Docker (for deployment)

## 📦 How to Run Locally

```bash
pip install flask
python app.py
```

Visit: `http://127.0.0.1:5000`

## 🐳 Docker Usage

```bash
docker build -t tribal-dances-app .
docker run -p 5000:5000 tribal-dances-app
```

## 📁 Project Structure

- `app.py` – Main application entry point
- `users.db` – SQLite database
- `static/` – Images and CSS/JS assets
- `templates/` – HTML templates (if present)
- `metadata.py` – Contains data for the portal

---
**Project by:** Sindhu Reddy  
**GitHub:** https://github.com/Sindhu2949/MiniProject_TribalDancesofIndia