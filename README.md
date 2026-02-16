# Kakuro Game - Iteration 1

Flask + HTML/CSS + SQLite implementation aligned to the Iteration-1 UML/use-case scope:

- Sign Up (Create Account)
- Login
- Start New Game (difficulty -> board generation -> game screen)
- Play Game (enter number -> validate move -> submit/check -> wrong-cell highlight -> result)
- Guest + Registered users can play
- SQLite is used for **authentication only** (`users` table)

## Tech Stack
=======
# Kakuro Game

- Python 3
- Flask
- Flask-Session (server-side session storage)
- SQLite (`sqlite3`)
- HTML/CSS + minimal JS
- pytest

## Project Structure

```text
kakuro/
  app.py
  config.py
  requirements.txt
  /models
    __init__.py
    user.py
    domain.py
  /services
    __init__.py
    auth_service.py
    game_service.py
    board_generator.py
    validation_service.py
  /db
    schema.sql
    kakuro.sqlite   # created automatically on first run
  /templates
    base.html
    welcome.html
    signup.html
    login.html
    main_menu.html
    difficulty.html
    game.html
  /static
    /css
      styles.css
    /js
      game.js
tests/
  conftest.py
  test_auth.py
  test_validation.py
```

## Setup

```bash
python -m venv venv
```

Windows PowerShell:

```bash
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
flask --app app run
```

Open:

```text
http://127.0.0.1:5000
```

## Tests

```bash
pytest
```

## Notes

- Database is auto-initialized from `kakuro/db/schema.sql` if missing.
- Active `GameSession`/`Board` are stored in Flask server-side session (iteration-1 scope).
- On `Check/Submit`, incorrect boards show:
  - visual highlight on wrong cells
  - wrong cell coordinates list `(row,col)`
- End-of-game action available: **New Game**.
- No timer/pause/save-load in Iteration 1.
