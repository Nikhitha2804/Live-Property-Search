# 🏠 Live Property Search

A full-stack real estate search application built with **Python (Flask)** and **PostgreSQL**. The application allows users to search over **600K+ property records** using keywords and advanced filters with fast server-side pagination.

## Features

- User registration and login
- Search properties by address, city, state, or postcode
- Advanced filters (price, bedrooms, property type)
- Property details page
- Server-side pagination
- Responsive Bootstrap UI
- RESTful APIs with AJAX for real-time search
- ETL pipeline to clean and load 600K+ records into PostgreSQL

---

## Tech Stack

- Python
- Flask
- PostgreSQL
- Pandas
- HTML
- CSS
- Bootstrap
- JavaScript
- jQuery
- AJAX

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Nikhitha2804/Live-Property-Search.git
cd Live-Property-Search
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

**Windows**

```bash
.venv\Scripts\activate
```

**Linux/macOS**

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Create a `.env` file

```env
DATABASE_URL=postgresql://username:password@localhost:5432/property_data
FLASK_SECRET_KEY=your_secret_key
```

### 6. Run the application

**Windows**

```powershell
$env:PYTHONPATH="src"
python -m live_property_search.app
```

**Linux/macOS**

```bash
export PYTHONPATH=src
python -m live_property_search.app
```

Open:

```
http://127.0.0.1:5001
```

---

## Project Structure

```
Live-Property-Search/
│
├── src/live_property_search/
│   ├── app.py
│   ├── db.py
│   ├── clean.py
│   ├── export.py
│   └── main.py
│
├── static/
├── templates/
├── data/
├── requirements.txt
├── README.md
└── .gitignore
```

---

## API Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | / | Home page |
| POST | /login | User login |
| POST | /register | User registration |
| GET | /api/properties | Fetch properties |
| POST | /api/search | Search properties |
| GET | /api/property/<id> | Property details |

---

## Project Highlights

- Cleaned and processed **600K+** property records using **Pandas**.
- Loaded cleaned data into **PostgreSQL** using a custom ETL pipeline.
- Implemented REST APIs with server-side pagination and AJAX-based search.
- Developed a responsive frontend using Bootstrap and JavaScript.

---

## Author

**Nikhitha Odela**

- GitHub: https://github.com/Nikhitha2804

---

## License

This project is created for educational and portfolio purposes.