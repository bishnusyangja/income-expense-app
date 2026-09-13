import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from tests.helpers import CSRF_HEADER_NAME, CSRF_URL, LOGIN_URL, REGISTER_URL
from finance.dbmodels import Expenditure, Income  # noqa: F401
from user.dbmodels import User  # noqa: F401


@pytest.fixture
def valid_payload() -> dict:
    return {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "address": "123 Main St",
        "phone": "5551234567",
        "password": "secret123",
    }


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def bare_client(db_engine):
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def client(bare_client):
    token = bare_client.get(CSRF_URL).json()["data"]["csrf_token"]
    bare_client.headers[CSRF_HEADER_NAME] = token
    return bare_client


@pytest.fixture
def registered_user(client, valid_payload):
    response = client.post(REGISTER_URL, json=valid_payload)
    assert response.status_code == 201
    return valid_payload


@pytest.fixture
def auth_client(client, registered_user):
    response = client.post(
        LOGIN_URL,
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    token = response.json()["data"]["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
