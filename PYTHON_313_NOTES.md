# Python 3.13 Compatibility Note

## Issue

There is currently a known compatibility issue between SQLAlchemy 2.0.x and Python 3.13 related to the `TypingOnly` class.

## Workaround Options

### Option 1: Use Python 3.12 (Recommended)

The easiest solution is to use Python 3.12 instead of Python 3.13:

1. Install Python 3.12
2. Recreate the virtual environment:
   ```powershell
   Remove-Item -Recurse -Force .venv
   python3.12 -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

### Option 2: Use Development Version of SQLAlchemy

Install the latest development version that has the fix:

```powershell
pip install git+https://github.com/sqlalchemy/sqlalchemy.git@main
```

### Option 3: Manual Initialization

Instead of using Flask-Migrate commands, you can manually initialize the database:

```python
from app import create_app, db

app = create_app()
with app.app_context():
    db.create_all()
    print("Database created successfully!")
```

Save this as `init_db.py` and run:
```powershell
C:/Users/zaid.kuba/LHUMS/.venv/Scripts/python.exe init_db.py
```

## Status

This issue is being tracked in SQLAlchemy and should be resolved in an upcoming release. For now, using Python 3.12 is the most stable approach for production systems.

## References

- SQLAlchemy Issue: https://github.com/sqlalchemy/sqlalchemy/issues/11277
- Python 3.13 Release Notes: https://docs.python.org/3.13/whatsnew/3.13.html
