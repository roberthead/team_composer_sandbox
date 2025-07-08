import uuid
from datetime import datetime

import pytest
from src.models.person import Person


class TestPersonModel:
    def test_person_creation(self):
        """Test creating a Person instance."""
        person = Person(
            login_id="jdoe",
            person_id="12345",
            name_first="John",
            name_middle="Q",
            name_last="Doe"
        )

        assert person.login_id == "jdoe"
        assert person.person_id == "12345"
        assert person.name_first == "John"
        assert person.name_middle == "Q"
        assert person.name_last == "Doe"

    def test_person_defaults(self):
        """Test Person model defaults."""
        person = Person()

        # ID is only generated when saved to database
        # For unit tests, we just check it starts as None
        assert person.id is None

        # Check string defaults (SQLAlchemy doesn't apply server_default in memory)
        # These will be empty strings in the database but None in memory
        assert person.login_id is None
        assert person.person_id is None
        assert person.name_first is None
        assert person.name_middle is None
        assert person.name_last is None

    def test_name_full_method(self):
        """Test the name_full() method."""
        # Test with all name parts
        person = Person(
            name_first="John",
            name_middle="Q",
            name_last="Doe"
        )
        assert person.name_full() == "John Q Doe"

        # Test with missing middle name
        person2 = Person(
            name_first="Jane",
            name_last="Smith"
        )
        assert person2.name_full() == "Jane Smith"

        # Test with empty names
        person3 = Person()
        assert person3.name_full() == ""

    def test_identifiers_method(self):
        """Test the identifiers() method."""
        test_id = uuid.uuid4()
        person = Person(
            id=test_id,
            login_id="jdoe",
            person_id="12345"
        )

        expected = f"{test_id}, jdoe, 12345"
        assert person.identifiers() == expected

    def test_repr_method(self):
        """Test the __repr__() method."""
        test_id = uuid.uuid4()
        person = Person(
            id=test_id,
            login_id="jdoe",
            name_first="John",
            name_middle="Q",
            name_last="Doe"
        )

        expected = f"<Person(id={test_id}, name='John Q Doe', login_id='jdoe')>"
        assert repr(person) == expected
