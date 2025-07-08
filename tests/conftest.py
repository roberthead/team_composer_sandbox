"""
Pytest configuration and fixtures for test suite.
Sets up test database and provides common fixtures.
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from src.main import app
from src.database.connection import get_db_session
from src.models.person import Base


# Use Rails-style test database naming
TEST_DATABASE_URL = "sqlite:///./team_composer_test.db"


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    return engine


@pytest.fixture(scope="session")
def tables(test_engine):
    """Create all tables in the test database."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_session(test_engine, tables):
    """Create a new database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_client(test_session):
    """Create a test client with the test database."""
    def override_get_db_session():
        try:
            yield test_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically set up test environment for all tests."""
    # Set test database URL
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    yield
    # Clean up
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]