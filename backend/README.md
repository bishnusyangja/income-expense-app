# Backend

FastAPI + SQLite API for income-expense-app.

## Run the server

From the project root:

```bash
./dev.sh
```

The API is available at http://127.0.0.1:8080. Docs: http://127.0.0.1:8080/docs.

## Run tests

```bash
uv run pytest
```

This runs every test in the `tests` package. Add `-v` for per-test names.

## Register a user

`POST /register` — email is used as the username.

Unsafe methods (`POST`, `PUT`, `PATCH`, `DELETE`) require a `csrf_token` cookie and a matching `X-CSRF-Token` header:

```bash
TOKEN=$(curl -s -c cookies.txt http://127.0.0.1:8080/csrf-token \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['csrf_token'])")

curl -X POST http://127.0.0.1:8080/register \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $TOKEN" \
  -d '{
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane@example.com",
    "address": "123 Main St",
    "phone": "5551234567",
    "password": "secret123"
  }'
```

## Log in

`POST /login` returns a JWT that expires in 30 days:

```bash
curl -X POST http://127.0.0.1:8080/login \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $TOKEN" \
  -d '{
    "email": "jane@example.com",
    "password": "secret123"
  }'
```

Set `JWT_SECRET` in the environment outside local development.

## Database migrations

Edit schemas in `user/dbmodels.py`. Migration files go in `alembic/versions/`.

```bash
uv run alembic revision --autogenerate -m "describe your change"
uv run alembic upgrade head
```
