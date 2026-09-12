# income-expense-app

Track income and expenses with a FastAPI backend and SQLite.

## Backend

The API lives in `backend/` and uses FastAPI, SQLAlchemy, and a local SQLite file (`backend/app.db`).

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

### Run the server

```bash
./dev.sh
```

The script installs dependencies, applies database migrations, then starts the API at [http://127.0.0.1:8080](http://127.0.0.1:8080). Interactive docs are at [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs).

### Register a user

`POST /register`

Email is stored as the username. Send first name, last name, email, address, phone, and password:

```bash
curl -X POST http://127.0.0.1:8080/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane@example.com",
    "address": "123 Main St",
    "phone": "5551234567",
    "password": "secret123"
  }'
```

### Database migrations

SQLAlchemy models live in `backend/app/models.py`. Changing a model does **not** update SQLite by itself.

Alembic migration scripts live in `backend/alembic/versions/`. After you change a model, generate and apply a migration from `backend/`:

```bash
cd backend
uv run alembic revision --autogenerate -m "describe your change"
uv run alembic upgrade head
```

`./dev.sh` also runs `alembic upgrade head` before starting the server.

If you still have an older `backend/app.db` from before the current `User` schema, delete that file and run `uv run alembic upgrade head` again (or just `./dev.sh`) to recreate it.
