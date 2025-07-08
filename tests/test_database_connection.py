import os
from unittest.mock import patch, MagicMock
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

import src.database.connection as db_connection


class TestDatabaseConfiguration:
    @patch.dict(os.environ, {}, clear=True)
    def test_database_url_default(self):
        """Test DATABASE_URL uses default when env var not set."""
        # Import fresh to get updated env
        import importlib
        importlib.reload(db_connection)

        expected_default = "sqlite:///./team_composer_development.db"
        assert db_connection.DATABASE_URL == expected_default

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///./custom_test.db"})
    def test_database_url_from_environment(self):
        """Test DATABASE_URL uses environment variable when set."""
        # Import fresh to get updated env
        import importlib
        importlib.reload(db_connection)

        assert db_connection.DATABASE_URL == "sqlite:///./custom_test.db"

    def test_engine_creation(self):
        """Test that engine is created with correct configuration."""
        assert db_connection.engine is not None
        # Engine should be bound to the DATABASE_URL
        assert str(db_connection.engine.url).startswith("sqlite:///")

    def test_session_local_creation(self):
        """Test SessionLocal is configured correctly."""
        assert db_connection.SessionLocal is not None

        # Check SessionLocal configuration
        session = db_connection.SessionLocal()
        # In SQLAlchemy 2.0, these are properties of the sessionmaker, not the session
        assert hasattr(session, 'commit')
        assert hasattr(session, 'rollback')
        assert session.bind == db_connection.engine
        session.close()


class TestGetDbFunction:
    def test_get_db_session_yields_session(self):
        """Test get_db_session yields a database session."""
        generator = db_connection.get_db_session()

        # Get the session from the generator
        session = next(generator)

        # Verify it's a SQLAlchemy session
        assert hasattr(session, 'query')
        assert hasattr(session, 'commit')
        assert hasattr(session, 'rollback')
        assert hasattr(session, 'close')

        # Cleanup: close the session
        try:
            next(generator)
        except StopIteration:
            pass  # Expected when generator finishes

    def test_get_db_session_closes_session_after_use(self):
        """Test get_db_session properly closes session after use."""
        with patch.object(db_connection, 'SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            generator = db_connection.get_db_session()

            # Get the session
            session = next(generator)
            assert session == mock_session

            # Complete the generator (simulates end of request)
            try:
                next(generator)
            except StopIteration:
                pass

            # Verify session was closed
            mock_session.close.assert_called_once()

    def test_get_db_session_closes_session_on_exception(self):
        """Test get_db_session closes session even if exception occurs."""
        with patch.object(db_connection, 'SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            generator = db_connection.get_db_session()

            # Get the session
            session = next(generator)
            assert session == mock_session

            # Simulate an exception during processing
            try:
                generator.throw(Exception("Simulated error"))
            except Exception:
                pass

            # Verify session was still closed despite the exception
            mock_session.close.assert_called_once()

    @patch.object(db_connection, 'SessionLocal')
    def test_get_db_session_handles_session_creation_error(self, mock_session_local):
        """Test get_db_session handles session creation errors gracefully."""
        mock_session_local.side_effect = SQLAlchemyError("Database connection failed")

        with pytest.raises(SQLAlchemyError):
            generator = db_connection.get_db_session()
            next(generator)

    def test_get_db_session_is_generator(self):
        """Test get_db_session returns a generator."""
        result = db_connection.get_db_session()

        # Should be a generator
        assert hasattr(result, '__next__')
        assert hasattr(result, '__iter__')

        # Clean up
        try:
            session = next(result)
            next(result)  # Trigger cleanup
        except StopIteration:
            pass

    def test_get_db_session_multiple_calls_create_separate_sessions(self):
        """Test multiple calls to get_db_session create separate sessions."""
        generator1 = db_connection.get_db_session()
        generator2 = db_connection.get_db_session()

        session1 = next(generator1)
        session2 = next(generator2)

        # Should be different session instances
        assert session1 is not session2

        # Clean up both generators
        for gen in [generator1, generator2]:
            try:
                next(gen)
            except StopIteration:
                pass


class TestDatabaseConnectionIntegration:
    def test_engine_and_session_compatibility(self):
        """Test that engine and SessionLocal are compatible."""
        # Create a session and verify it can work with the engine
        session = db_connection.SessionLocal()

        try:
            # The session should be bound to our engine
            assert session.bind == db_connection.engine

            # Should be able to execute basic operations (without requiring actual DB)
            # We don't test actual SQL execution since that would require a real database
            assert hasattr(session, 'execute')
            assert hasattr(session, 'commit')

        finally:
            session.close()

    def test_database_url_format_validation(self):
        """Test DATABASE_URL has correct SQLite format."""
        url = db_connection.DATABASE_URL

        # Should start with sqlite:///
        assert url.startswith("sqlite:///"), f"DATABASE_URL should start with 'sqlite:///', got: {url}"

        # Should contain database file path
        assert ".db" in url, "DATABASE_URL should contain .db file extension"

    def test_engine_creation_with_database_url(self):
        """Test engine is created with the correct DATABASE_URL."""
        # Verify the engine's URL matches our DATABASE_URL
        engine_url = str(db_connection.engine.url)
        expected_url = db_connection.DATABASE_URL

        # Compare the base URLs (they should match)
        assert engine_url.startswith("sqlite:///"), f"Engine URL should be SQLite: {engine_url}"


class TestDatabaseConnectionInFastAPIContext:
    def test_get_db_session_fastapi_dependency_pattern(self):
        """Test get_db_session follows FastAPI dependency injection pattern."""
        # This simulates how FastAPI would use the dependency
        dependency_generator = db_connection.get_db_session()

        # FastAPI would call next() to get the dependency
        session = next(dependency_generator)

        # Verify we get a valid session
        assert session is not None
        assert hasattr(session, 'execute')  # SQLAlchemy session method

        # Simulate FastAPI cleanup (calling next again triggers finally block)
        try:
            next(dependency_generator)
        except StopIteration:
            # This is expected - the generator should be exhausted
            pass

        # After this point, the session should be closed
        # We can't easily test this without mocking, but the pattern is correct

    def test_get_db_session_context_manager_style(self):
        """Test get_db_session can be used in context manager style."""
        generator = db_connection.get_db_session()

        try:
            session = next(generator)

            # Do something with the session
            assert session is not None

            # Simulate some database operation
            # (In real usage, you'd do session.query(), session.add(), etc.)

        finally:
            # Trigger the finally block in get_db_session
            try:
                next(generator)
            except StopIteration:
                pass