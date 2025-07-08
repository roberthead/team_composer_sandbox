import uuid
from datetime import datetime
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from src.schemas.person import PersonBase, PersonCreate, PersonUpdate, Person


class TestPersonBase:
    def test_person_base_creation_with_defaults(self):
        """Test PersonBase with default values."""
        person = PersonBase()

        assert person.login_id == ""
        assert person.person_id == ""
        assert person.name_first == ""
        assert person.name_middle == ""
        assert person.name_last == ""

    def test_person_base_creation_with_values(self):
        """Test PersonBase with provided values."""
        person = PersonBase(
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

    def test_person_base_partial_values(self):
        """Test PersonBase with partial values."""
        person = PersonBase(
            name_first="Jane",
            name_last="Smith"
        )

        assert person.name_first == "Jane"
        assert person.name_last == "Smith"
        assert person.login_id == ""
        assert person.person_id == ""
        assert person.name_middle == ""

    def test_person_base_dict_conversion(self):
        """Test PersonBase to dict conversion."""
        person = PersonBase(
            login_id="jdoe",
            person_id="12345",
            name_first="John",
            name_last="Doe"
        )

        expected = {
            "login_id": "jdoe",
            "person_id": "12345",
            "name_first": "John",
            "name_middle": "",
            "name_last": "Doe"
        }

        assert person.model_dump() == expected

    def test_person_base_json_serialization(self):
        """Test PersonBase JSON serialization."""
        person = PersonBase(
            login_id="jdoe",
            name_first="John",
            name_last="Doe"
        )

        json_str = person.model_dump_json()
        assert '"login_id":"jdoe"' in json_str
        assert '"name_first":"John"' in json_str
        assert '"name_last":"Doe"' in json_str


class TestPersonCreate:
    def test_person_create_inherits_from_base(self):
        """Test PersonCreate inherits all PersonBase functionality."""
        person = PersonCreate(
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

    def test_person_create_with_defaults(self):
        """Test PersonCreate with default values."""
        person = PersonCreate()

        assert person.login_id == ""
        assert person.person_id == ""
        assert person.name_first == ""
        assert person.name_middle == ""
        assert person.name_last == ""


class TestPersonUpdate:
    def test_person_update_all_none_by_default(self):
        """Test PersonUpdate has all None defaults."""
        person = PersonUpdate()

        assert person.login_id is None
        assert person.person_id is None
        assert person.name_first is None
        assert person.name_middle is None
        assert person.name_last is None

    def test_person_update_partial_fields(self):
        """Test PersonUpdate with only some fields."""
        person = PersonUpdate(
            name_first="Jane",
            login_id="jsmith"
        )

        assert person.name_first == "Jane"
        assert person.login_id == "jsmith"
        assert person.name_last is None
        assert person.person_id is None
        assert person.name_middle is None

    def test_person_update_empty_strings(self):
        """Test PersonUpdate accepts empty strings."""
        person = PersonUpdate(
            name_first="",
            login_id=""
        )

        assert person.name_first == ""
        assert person.login_id == ""

    def test_person_update_dict_excludes_none(self):
        """Test PersonUpdate dict excludes None values when needed."""
        person = PersonUpdate(
            name_first="Jane",
            login_id="jsmith"
        )

        # Include None values
        full_dict = person.model_dump()
        assert full_dict["name_first"] == "Jane"
        assert full_dict["login_id"] == "jsmith"
        assert full_dict["name_last"] is None

        # Exclude None values
        filtered_dict = person.model_dump(exclude_none=True)
        assert filtered_dict == {
            "name_first": "Jane",
            "login_id": "jsmith"
        }


class TestPerson:
    def test_person_with_all_fields(self):
        """Test Person schema with all required fields."""
        test_id = str(str(uuid.uuid4()))
        test_created = datetime.now()
        test_updated = datetime.now()

        person = Person(
            id=test_id,
            login_id="jdoe",
            person_id="12345",
            name_first="John",
            name_middle="Q",
            name_last="Doe",
            created_at=test_created,
            updated_at=test_updated
        )

        assert person.id == test_id
        assert person.login_id == "jdoe"
        assert person.person_id == "12345"
        assert person.name_first == "John"
        assert person.name_middle == "Q"
        assert person.name_last == "Doe"
        assert person.created_at == test_created
        assert person.updated_at == test_updated

    def test_person_without_updated_at(self):
        """Test Person schema without updated_at (optional field)."""
        test_id = str(uuid.uuid4())
        test_created = datetime.now()

        person = Person(
            id=test_id,
            login_id="jdoe",
            person_id="12345",
            name_first="John",
            name_last="Doe",
            created_at=test_created
        )

        assert person.updated_at is None

    def test_person_missing_required_fields(self):
        """Test Person schema fails without required fields."""
        with pytest.raises(ValidationError) as exc_info:
            Person(
                login_id="jdoe",
                name_first="John"
                # Missing id and created_at
            )

        errors = exc_info.value.errors()
        error_fields = [error["loc"][0] for error in errors]
        assert "id" in error_fields
        assert "created_at" in error_fields

    def test_person_invalid_uuid(self):
        """Test Person schema accepts string ID (SQLite compatibility)."""
        # With SQLite, ID is a string, so "not-a-uuid" is valid
        person = Person(
            id="not-a-uuid",
            login_id="jdoe",
            name_first="John",
            name_last="Doe",
            created_at=datetime.now()
        )
        assert person.id == "not-a-uuid"

    def test_person_invalid_datetime(self):
        """Test Person schema fails with invalid datetime."""
        with pytest.raises(ValidationError) as exc_info:
            Person(
                id=str(uuid.uuid4()),
                login_id="jdoe",
                name_first="John",
                name_last="Doe",
                created_at="not-a-datetime"
            )

        errors = exc_info.value.errors()
        assert any(error["loc"][0] == "created_at" for error in errors)

    def test_person_from_attributes_config(self):
        """Test Person schema has from_attributes config for ORM compatibility."""
        # This tests that the Config class exists and has the right setting
        assert hasattr(Person, "model_config")
        # In Pydantic v2, from_attributes is part of model_config
        assert Person.model_config.get("from_attributes") is True

    def test_person_json_serialization(self):
        """Test Person JSON serialization with ID and datetime."""
        test_id = str(uuid.uuid4())
        test_created = datetime(2023, 1, 1, 12, 0, 0)

        person = Person(
            id=test_id,
            login_id="jdoe",
            name_first="John",
            name_last="Doe",
            created_at=test_created
        )

        json_data = person.model_dump()
        assert json_data["id"] == test_id
        assert json_data["created_at"] == test_created

        # Test JSON string serialization
        json_str = person.model_dump_json()
        assert str(test_id) in json_str
        assert "jdoe" in json_str


class TestSchemaInteraction:
    def test_person_create_to_person_conversion(self):
        """Test converting PersonCreate to Person (simulating API flow)."""
        person_create = PersonCreate(
            login_id="jdoe",
            person_id="12345",
            name_first="John",
            name_last="Doe"
        )

        # Simulate what happens after database save
        test_id = str(uuid.uuid4())
        test_created = datetime.now()

        person = Person(
            id=test_id,
            created_at=test_created,
            **person_create.model_dump()
        )

        assert person.id == test_id
        assert person.created_at == test_created
        assert person.login_id == "jdoe"
        assert person.person_id == "12345"
        assert person.name_first == "John"
        assert person.name_last == "Doe"

    def test_person_update_merge(self):
        """Test merging PersonUpdate with existing data."""
        # Existing person data
        existing_data = {
            "login_id": "old_login",
            "person_id": "12345",
            "name_first": "John",
            "name_middle": "Q",
            "name_last": "Doe"
        }

        # Update data
        update = PersonUpdate(
            name_first="Jane",
            login_id="new_login"
        )

        # Merge logic (exclude None values from update)
        update_dict = update.model_dump(exclude_none=True)
        merged_data = {**existing_data, **update_dict}

        assert merged_data["name_first"] == "Jane"  # Updated
        assert merged_data["login_id"] == "new_login"  # Updated
        assert merged_data["name_last"] == "Doe"  # Unchanged
        assert merged_data["person_id"] == "12345"  # Unchanged