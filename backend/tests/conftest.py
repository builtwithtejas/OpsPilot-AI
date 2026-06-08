# backend/tests/conftest.py
# Sets up an isolated in-memory SQLite database for every test session.
# This ensures tests never touch your real database and are fully isolated.
#
# Add this file to backend/tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.database.dependencies import get_db
from app.main import app

# In-memory SQLite for tests — fast, isolated, disposable
TEST_DATABASE_URL = "sqlite:///./test_opspilot.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables once for the test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def override_db():
    """Override the DB dependency for every test."""
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
