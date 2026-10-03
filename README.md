# Career Pathway Analysis System
## Web-Based Career Pathway Analysis System Using Academic and Interest Profiling
**Student:** Michael Gathigi Wanjiru | **Reg:** IC211-0100/2022  
**Supervisor:** Solomon Mwanjele | **Degree:** BSc. Information Technology

---

## QUICK SETUP GUIDE

### Prerequisites
- Python 3.12+ installed
- MySQL Server installed and running
- Git (optional)

---

### STEP 1 — Install Python Dependencies

Open your terminal/command prompt in the project folder:

```bash
pip install -r requirements.txt
```

> If mysqlclient fails, try: `pip install PyMySQL` and add this to `career_system/__init__.py`:
> ```python
> import pymysql
> pymysql.install_as_MySQLdb()
> ```

---

### STEP 2 — Create MySQL Database

Open MySQL terminal or MySQL Workbench and run:

```sql
CREATE DATABASE career_pathway_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Then update `career_system/settings.py` with your MySQL credentials:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'career_pathway_db',
        'USER': 'root',       # your MySQL username
        'PASSWORD': '',       # your MySQL password
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

> **ALTERNATIVE (SQLite for quick testing):**  
> Comment out the MySQL block in settings.py and uncomment the SQLite block.  
> No database setup needed for SQLite.

---

### STEP 3 — Run Database Migrations

```bash
python manage.py makemigrations accounts
python manage.py makemigrations core
python manage.py migrate
```

---

### STEP 4 — Seed the Database

This loads all career clusters, subjects, weights, RIASEC questions, institutions, courses, and labor market data:

```bash
python manage.py seed_data
```

Expected output:
```
Starting database seeding...
  Subjects: 21 created
  Career Clusters: 10 created
  Cluster-Subject Weights: 67 created
  RIASEC Questions: 30 created
  Institutions: 25 created
  Courses: 32 created
  Labor Market Data: 10 created
✓ Database seeded successfully!
```

---

### STEP 5 — Create Admin Account

```bash
python manage.py createsuperuser
```
Follow the prompts to create an admin username, email, and password.

---

### STEP 6 — Run the Development Server

```bash
python manage.py runserver
```

Then open your browser and visit:
- **Main App:** http://127.0.0.1:8000/
- **Admin Panel:** http://127.0.0.1:8000/admin/

---

## SYSTEM WORKFLOW

1. **Register** at `/accounts/register/`
2. **Enter KCSE grades** at `/grades/`
3. **Take the RIASEC quiz** at `/quiz/`
4. **View results** at `/results/`
5. **Download PDF report** at `/download-report/`

---

## PROJECT FILE STRUCTURE

```
career_system/
├── manage.py
├── requirements.txt
├── README.md
│
├── career_system/          # Django project config
│   ├── settings.py         # All settings & constants
│   ├── urls.py             # Master URL routing
│   └── wsgi.py
│
├── accounts/               # Authentication app
│   ├── models.py           # StudentUser (custom user model)
│   ├── forms.py            # Registration & login forms
│   ├── views.py            # Register, login, logout, profile
│   ├── urls.py
│   └── admin.py
│
├── core/                   # Main system app
│   ├── models.py           # All 12 database models
│   ├── engine.py           # ★ Recommendation engine (core algorithms)
│   ├── pdf_generator.py    # PDF report generator (ReportLab)
│   ├── views.py            # Dashboard, grades, quiz, results, PDF
│   ├── urls.py
│   ├── admin.py
│   ├── templatetags/
│   │   └── custom_filters.py
│   └── management/
│       └── commands/
│           └── seed_data.py   # Database seeding command
│
└── templates/
    ├── base.html              # Master layout + navbar + footer
    ├── accounts/
    │   ├── register.html
    │   └── login.html
    └── core/
        ├── landing.html       # Public landing page
        ├── dashboard.html     # Student dashboard with progress
        ├── grades_entry.html  # KCSE grade input form
        ├── quiz.html          # 30-question RIASEC quiz
        └── results.html       # Career recommendations + charts
```

---

## RECOMMENDATION ENGINE SUMMARY

The engine (`core/engine.py`) implements three algorithms:

**Algorithm 1 — Academic Score (per cluster):**
```
Score(C) = Σ[grade_points × subject_weight] / Σ[12 × subject_weight] × 100
```

**Algorithm 2 — RIASEC Score (per type):**
```
Score(T) = Σ[quiz_responses for type T] / 25 × 100
```

**Algorithm 3 — Interest Score (per cluster):**
```
Interest(C) = Σ[RIASEC_score(T) × affinity_weight(C, T)]
```

**Final Combined Score:**
```
Combined(C) = Academic(C) × 0.60 + Interest(C) × 0.40
             [- 5.0 if cluster is Saturated]
```

---

## TESTING

Run the built-in Django tests:
```bash
python manage.py test
```

For manual testing, create a test student via the registration page.

---

## ADMIN PANEL FEATURES

Access at `/admin/` with your superuser credentials:
- View/edit all students and their results
- Manage career clusters, courses, institutions
- Update labor market data
- View RIASEC quiz responses
- Edit subject weights (tune the recommendation engine)

---

## DATA SOURCES

| Data | Source |
|---|---|
| KCSE Grade Scale | KUCCPS Official Guidelines |
| Career Clusters | Adapted from KUCCPS Cluster System |
| Course Requirements | KUCCPS 2023 Booklet |
| TVET Programs | TVETA Registry |
| Labor Market Data | KNBS Economic Survey 2023, KEPSA Skills Report |
| RIASEC Model | Holland (1997) Occupational Theory |
| Salary Data | Brighter Monday Kenya, KNBS Wage Report |

---

## TECHNOLOGIES USED

| Component | Technology | Version |
|---|---|---|
| Backend | Python + Django | 6.0.3 |
| Database | MySQL | 8.0+ |
| PDF Generation | ReportLab | 4.4.10 |
| Frontend | Bootstrap 5 | 5.3.0 |
| Icons | Bootstrap Icons | 1.11.0 |
| Charts | Chart.js | 4.4.0 |
| Fonts | Google Fonts (Sora + DM Sans) | — |

---

*Final Year Project — Department of Information Technology*
