# 🏠 Live Property Search

A full-stack real estate search platform built using **Python (Flask)** and **PostgreSQL** that enables users to search and explore **599,000+ US housing properties** with advanced filtering, secure authentication, and a responsive web interface.

---

## 🚀 Features

- 🔐 User Registration & Login Authentication
- 🏡 Search over **599K+ property listings**
- 🔍 Advanced filtering by:
  - City
  - Postcode
  - Price Range
  - Bedrooms
  - Property Type
- ⚡ AJAX-based real-time search without page refresh
- 📄 RESTful APIs for property search and details
- 📊 Server-side pagination for efficient large dataset handling
- 💾 PostgreSQL database integration
- 📱 Responsive UI built with Bootstrap 5

---

## 🛠️ Tech Stack

### Backend
- Python
- Flask
- PostgreSQL
- psycopg2

### Frontend
- HTML5
- CSS3
- Bootstrap 5
- JavaScript
- jQuery
- AJAX

### Data Processing
- Pandas
- NumPy

### Authentication
- Flask-Login

### Environment
- python-dotenv

---

## 📂 Project Structure

```
Live-Property-Search/
│
├── data/
│   └── random_records_sample.csv
│
├── src/
│   └── live_property_search/
│       ├── app.py
│       ├── db.py
│       ├── export.py
│       ├── clean.py
│       └── __init__.py
│
├── static/
│   ├── script.js
│   └── style.css
│
├── templates/
│   ├── index.html
│   ├── login.html
│   └── register.html
│
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

---

## 📊 Dataset

- **Source:** Kaggle – US Housing Properties Dataset
- **Records:** 599,511+ cleaned property listings
- **Database:** PostgreSQL

The ETL pipeline performs:

- Duplicate removal
- Missing value handling
- Data type conversion
- Feature engineering
- Data cleaning and preprocessing
- PostgreSQL data loading

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/Live-Property-Search.git
cd Live-Property-Search
```

---

### 2. Create a virtual environment

```bash
python -m venv .venv
```

---

### 3. Activate the virtual environment

**Windows**

```bash
.venv\Scripts\activate
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

---

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 5. Configure Environment Variables

Create a `.env` file in the project root.

```env
DATABASE_URL=postgresql://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/property_data

FLASK_SECRET_KEY=your_secret_key
```

---

### 6. Import the Dataset

Run the export script to create the database table and import the cleaned dataset.

```bash
python src/live_property_search/export.py
```

---

### 7. Run the Application

**Windows**

```bash
set PYTHONPATH=src
python -m live_property_search.app
```

**PowerShell**

```powershell
$env:PYTHONPATH="src"
python -m live_property_search.app
```

**Linux / macOS**

```bash
export PYTHONPATH=src
python -m live_property_search.app
```

---

Open your browser:

```
http://127.0.0.1:5001
```

---

## 📌 REST API Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | / | Home Page |
| GET | /login | Login Page |
| POST | /login | User Login |
| GET | /register | Register Page |
| POST | /register | User Registration |
| GET | /logout | Logout |
| GET | /api/properties | Fetch Properties |
| POST | /api/search | Search Properties |
| GET | /api/property/<property_id> | Property Details |

---

## 📸 Screenshots

### Login Page

_Add screenshot here_

### Property Search

_Add screenshot here_

### Search Results

_Add screenshot here_

### Property Details

_Add screenshot here_

---

## 📈 Future Enhancements

- Google Maps Integration
- Property Image Gallery
- Favorite Properties
- Advanced Sorting
- Price Trend Analysis
- Recommendation System

---

## 👨‍💻 Author

**Nikhitha Odela**

GitHub: https://github.com/<your-username>

LinkedIn: https://linkedin.com/in/<your-linkedin>

---

## 📄 License

This project was developed for educational and portfolio purposes.