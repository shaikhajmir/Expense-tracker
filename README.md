# Expense Tracker (Flask)

## Quick start

1. Create a virtualenv and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # on Windows: venv\Scripts\activate
   ```

2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Change `SECRET_KEY` in config.py.

4. Run the app:
   ```bash
   python app.py
   ```

5. Open http://127.0.0.1:5000

## Features
- Signup / Login
- Add / Edit / Delete expenses
- Filter expenses by date/category
- Dashboard with category pie chart and recent expenses

## Notes
- Database `expenses.db` is created automatically in the project folder on first run.
- For production, use a proper database (Postgres/MySQL) and set `SECRET_KEY` securely.
