# Backend

FastAPI + SQLite API for income-expense-app.

## Run the server

From the project root:

```bash
./dev.sh
```

The API is available at http://127.0.0.1:8080. Docs: http://127.0.0.1:8080/docs.

## Register a user

`POST /register` — email is used as the username.

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

## Database migrations

Edit schemas in `user/dbmodels.py`. Migration files go in `alembic/versions/`.

```bash
uv run alembic revision --autogenerate -m "describe your change"
uv run alembic upgrade head
```
