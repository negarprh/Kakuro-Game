# Kakuro Game – Iteration 1 (MVP)

A local web application scaffold for a Kakuro puzzle game built with:

- **Backend:** Python 3 + Flask
- **Database:** SQLite + SQLAlchemy
- **Frontend:** Jinja templates (HTML) + CSS
- **Architecture:** MVC-style separation (routes, services, repositories, models)
- **Testing:** pytest

Runs locally on `localhost`.

---

## Iteration 1 Features

### Authentication & Modes

- Welcome page:
  - Continue as Guest
  - Sign Up
  - Log In

- Registered users:
  - Unique username
  - Unique email
  - Password hashing using `werkzeug.security`

- Guest mode:
  - Can play normally
  - Cannot save results
  - No persistence

---

### Game Flow

- Main Menu:
  - Start New Game
  - Leaderboard (placeholder)
  - Log Out (registered users)

- Difficulty selection:
  - Easy → `4x4`
  - Medium → `7x7`
  - Hard → `10x10`

- Game page:
  - Rendered Kakuro grid
  - Digit inputs (1–9)
  - Submit / Check button
  - Feedback messages (invalid / win)

---

### Validation Rules

- Only digits `1–9` allowed
- No duplicate digits in a single run
- If a run is complete → sum must match clue
- Win condition:
  - All playable cells filled
  - All runs valid

---

## Project Structure

```
kakuro/
│
├── routes/        # Flask blueprints (main, auth, game)
├── services/      # Auth, board generation, validation logic
├── repositories/  # Database operations
├── models/        # SQLAlchemy models
├── templates/     # Jinja templates
├── static/        # CSS and assets
│
tests/             # pytest unit tests
app.py             # Flask entry point
requirements.txt
```

---

## Session Storage (Iteration 1)

Game state is stored in the Flask session:

- `current_board`
- `current_solution`
- `difficulty`
- `user_mode`

No save/load functionality in this iteration.

---

## Setup & Run (Windows – PowerShell)

### 1️⃣ Create virtual environment

```bash
py -m venv venv
```

### 2️⃣ Activate virtual environment

```bash
.\venv\Scripts\Activate.ps1
```

If blocked:

```bash
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

### 3️⃣ Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

### 4️⃣ Run the application

Recommended (avoids PATH issues):

```bash
python -m flask --app app run --debug
```

Then open:

```
http://127.0.0.1:5000
```

---

## Run Tests

```bash
python -m pytest
```

---

## Optional Database Initialization

Tables are auto-created at startup.

You may also run:

```bash
python -m flask --app app init-db
```

---

## Assumptions

- The board generator is a prototype for Iteration 1.
- Boards are valid-looking but not optimized for puzzle quality.
- Difficulty sizes are fixed (`4x4`, `7x7`, `10x10`).
- Leaderboard is placeholder only.
- Guest sessions are not stored in the database.

---

## Not Implemented in Iteration 1

- Pause/blur
- Timer
- Save/load game
- Real leaderboard logic
- Profile management
- Persistent settings

---
