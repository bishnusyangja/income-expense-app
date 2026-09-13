import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from tests.helpers import CSRF_HEADER_NAME, CSRF_URL
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
