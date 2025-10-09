# Alvarez Bakery — Sales Forecasting & Management (POS)

Roles implemented:
- **Admin (Owner)**: Full access (Products CRUD, Sales, Forecast & Analytics, Reports export)
- **Cashier (Staff)**: POS only (create sales, discounts, receipt printing)

Quick start (SQLite):
```bash
cd alvarez_bakery
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
# (Optional) seed demo data
python manage.py seed_demo
python manage.py runserver
```

Login at http://127.0.0.1:8000
- Use the superuser for Admin access. To create a cashier, create a standard user (not staff).
  Cashiers can log in and use the POS, but can't access products, reports, or forecast pages.

Switch to MySQL:
- In `alvarez_bakery/settings.py`, replace the `DATABASES` section with the MySQL block and set your creds.
- Install MySQL server locally and ensure `pip install mysqlclient` worked.
- Then run `python manage.py migrate` again.
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "alvarez_bakery",
        "USER": "root",
        "PASSWORD": "yourpassword",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": {"charset": "utf8mb4"},
    }
}
```
