import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.person import Person
from src.schemas.person import PersonCreate, PersonUpdate
from src.services.person_service import PersonService


class TestPersonService:
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def person_service(self, mock_session):
        """Create a PersonService instance with mock session."""
        return PersonService(mock_session)

    @pytest.fixture
    def sample_person(self):
        """Create a sample person for testing."""
        return Person(
            id=str(uuid.uuid4()),
            login_id="jdoe",
            person_id="12345",
            name_first="John",
            name_middle="Q",
            name_last="Doe",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @pytest.fixture
    def sample_person_create(self):
        """Create sample person creation data."""
        return PersonCreate(
            login_id="jdoe",
            person_id="12345",
            name_first="John",
            name_middle="Q",
            name_last="Doe"
        )

    @pytest.fixture
    def sample_person_update(self):
        """Create sample person update data."""
        return PersonUpdate(
            name_first="Jane",
            login_id="jsmith"
        )


class TestPersonServiceInit(TestPersonService):
    def test_init_with_session(self, mock_session):
        """Test PersonService initialization with session."""
        service = PersonService(mock_session)
        assert service.db == mock_session


class TestCreatePerson(TestPersonService):
    def test_create_person_success(self, person_service, mock_session, sample_person_create, sample_person):
        """Test successful person creation."""
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Mock the Person constructor to return our sample person
        with patch('src.services.person_service.Person', return_value=sample_person):
            result = person_service.create_person(sample_person_create)

        assert result == sample_person
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(sample_person)

    def test_create_person_integrity_error(self, person_service, mock_session, sample_person_create):
        """Test person creation with integrity error."""
        mock_session.add.return_value = None
        mock_session.commit.side_effect = IntegrityError("Duplicate key", None, None)
        mock_session.rollback.return_value = None

        with pytest.raises(ValueError, match="Person creation failed"):
            person_service.create_person(sample_person_create)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()


class TestGetPersonById(TestPersonService):
    def test_get_person_by_id_success(self, person_service, mock_session, sample_person):
        """Test getting person by ID successfully."""
        person_id = str(uuid.uuid4())
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_person

        result = person_service.get_person_by_id(person_id)

        assert result == sample_person
        mock_session.query.assert_called_once_with(Person)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

    def test_get_person_by_id_not_found(self, person_service, mock_session):
        """Test getting person by ID when not found."""
        person_id = str(uuid.uuid4())
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        result = person_service.get_person_by_id(person_id)

        assert result is None


class TestGetPersonByMayoLoginId(TestPersonService):
    def test_get_person_by_mayo_login_id_success(self, person_service, mock_session, sample_person):
        """Test getting person by Mayo login ID successfully."""
        login_id = "jdoe"
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_person

        result = person_service.get_person_by_mayo_login_id(login_id)

        assert result == sample_person
        mock_session.query.assert_called_once_with(Person)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

    def test_get_person_by_mayo_login_id_not_found(self, person_service, mock_session):
        """Test getting person by Mayo login ID when not found."""
        login_id = "nonexistent"
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        result = person_service.get_person_by_mayo_login_id(login_id)

        assert result is None


class TestGetPersonByMayoPersonId(TestPersonService):
    def test_get_person_by_mayo_person_id_success(self, person_service, mock_session, sample_person):
        """Test getting person by Mayo person ID successfully."""
        person_id = "12345"
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_person

        result = person_service.get_person_by_mayo_person_id(person_id)

        assert result == sample_person
        mock_session.query.assert_called_once_with(Person)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

    def test_get_person_by_mayo_person_id_not_found(self, person_service, mock_session):
        """Test getting person by Mayo person ID when not found."""
        person_id = "nonexistent"
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        result = person_service.get_person_by_mayo_person_id(person_id)

        assert result is None


class TestGetPeople(TestPersonService):
    def test_get_people_default_params(self, person_service, mock_session, sample_person):
        """Test getting people with default parameters."""
        mock_query = MagicMock()
        mock_offset = MagicMock()
        mock_limit = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit
        mock_limit.all.return_value = [sample_person]

        result = person_service.get_people()

        assert result == [sample_person]
        mock_session.query.assert_called_once_with(Person)
        mock_query.offset.assert_called_once_with(0)
        mock_offset.limit.assert_called_once_with(100)
        mock_limit.all.assert_called_once()

    def test_get_people_custom_params(self, person_service, mock_session, sample_person):
        """Test getting people with custom parameters."""
        mock_query = MagicMock()
        mock_offset = MagicMock()
        mock_limit = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit
        mock_limit.all.return_value = [sample_person]

        result = person_service.get_people(skip=10, limit=5)

        assert result == [sample_person]
        mock_query.offset.assert_called_once_with(10)
        mock_offset.limit.assert_called_once_with(5)


class TestSearchPeopleByName(TestPersonService):
    def test_search_people_by_name_success(self, person_service, mock_session, sample_person):
        """Test searching people by name successfully."""
        name_query = "John"
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_offset = MagicMock()
        mock_limit = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit
        mock_limit.all.return_value = [sample_person]

        result = person_service.search_people_by_name(name_query)

        assert result == [sample_person]
        mock_session.query.assert_called_once_with(Person)
        mock_query.filter.assert_called_once()
        mock_filter.offset.assert_called_once_with(0)
        mock_offset.limit.assert_called_once_with(100)
        mock_limit.all.assert_called_once()

    def test_search_people_by_name_custom_params(self, person_service, mock_session, sample_person):
        """Test searching people by name with custom parameters."""
        name_query = "Jane"
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_offset = MagicMock()
        mock_limit = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit
        mock_limit.all.return_value = [sample_person]

        result = person_service.search_people_by_name(name_query, skip=5, limit=10)

        assert result == [sample_person]
        mock_filter.offset.assert_called_once_with(5)
        mock_offset.limit.assert_called_once_with(10)


class TestUpdatePerson(TestPersonService):
    def test_update_person_success(self, person_service, mock_session, sample_person, sample_person_update):
        """Test successful person update."""
        person_id = str(uuid.uuid4())

        # Mock get_person_by_id to return existing person
        with patch.object(person_service, 'get_person_by_id', return_value=sample_person):
            mock_session.commit.return_value = None
            mock_session.refresh.return_value = None

            result = person_service.update_person(person_id, sample_person_update)

            assert result == sample_person
            assert sample_person.name_first == "Jane"
            assert sample_person.login_id == "jsmith"
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once_with(sample_person)

    def test_update_person_not_found(self, person_service, mock_session, sample_person_update):
        """Test person update when person not found."""
        person_id = str(uuid.uuid4())

        # Mock get_person_by_id to return None
        with patch.object(person_service, 'get_person_by_id', return_value=None):
            result = person_service.update_person(person_id, sample_person_update)

            assert result is None
            mock_session.commit.assert_not_called()

    def test_update_person_integrity_error(self, person_service, mock_session, sample_person, sample_person_update):
        """Test person update with integrity error."""
        person_id = str(uuid.uuid4())

        # Mock get_person_by_id to return existing person
        with patch.object(person_service, 'get_person_by_id', return_value=sample_person):
            mock_session.commit.side_effect = IntegrityError("Duplicate key", None, None)
            mock_session.rollback.return_value = None

            with pytest.raises(ValueError, match="Person update failed"):
                person_service.update_person(person_id, sample_person_update)

            mock_session.commit.assert_called_once()
            mock_session.rollback.assert_called_once()


class TestDeletePerson(TestPersonService):
    def test_delete_person_success(self, person_service, mock_session, sample_person):
        """Test successful person deletion."""
        person_id = str(uuid.uuid4())

        # Mock get_person_by_id to return existing person
        with patch.object(person_service, 'get_person_by_id', return_value=sample_person):
            mock_session.delete.return_value = None
            mock_session.commit.return_value = None

            result = person_service.delete_person(person_id)

            assert result is True
            mock_session.delete.assert_called_once_with(sample_person)
            mock_session.commit.assert_called_once()

    def test_delete_person_not_found(self, person_service, mock_session):
        """Test person deletion when person not found."""
        person_id = str(uuid.uuid4())

        # Mock get_person_by_id to return None
        with patch.object(person_service, 'get_person_by_id', return_value=None):
            result = person_service.delete_person(person_id)

            assert result is False
            mock_session.delete.assert_not_called()
            mock_session.commit.assert_not_called()


class TestCountPeople(TestPersonService):
    def test_count_people(self, person_service, mock_session):
        """Test counting people."""
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.count.return_value = 42

        result = person_service.count_people()

        assert result == 42
        mock_session.query.assert_called_once_with(Person)
        mock_query.count.assert_called_once()


class TestPersonExistsByMayoIds(TestPersonService):
    def test_person_exists_by_mayo_login_id_true(self, person_service, mock_session, sample_person):
        """Test person exists by Mayo login ID returns True."""
        login_id = "jdoe"
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_person

        result = person_service.person_exists_by_mayo_ids(login_id=login_id)

        assert result is True
        mock_session.query.assert_called_once_with(Person)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

    def test_person_exists_by_mayo_login_id_false(self, person_service, mock_session):
        """Test person exists by Mayo login ID returns False."""
        login_id = "nonexistent"
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        result = person_service.person_exists_by_mayo_ids(login_id=login_id)

        assert result is False

    def test_person_exists_by_mayo_person_id_true(self, person_service, mock_session, sample_person):
        """Test person exists by Mayo person ID returns True."""
        person_id = "12345"
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_person

        result = person_service.person_exists_by_mayo_ids(person_id=person_id)

        assert result is True
        mock_session.query.assert_called_once_with(Person)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

    def test_person_exists_by_mayo_person_id_false(self, person_service, mock_session):
        """Test person exists by Mayo person ID returns False."""
        person_id = "nonexistent"
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        result = person_service.person_exists_by_mayo_ids(person_id=person_id)

        assert result is False

    def test_person_exists_by_both_ids_true(self, person_service, mock_session, sample_person):
        """Test person exists by both Mayo IDs returns True."""
        login_id = "jdoe"
        person_id = "12345"
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_person

        result = person_service.person_exists_by_mayo_ids(
            login_id=login_id,
            person_id=person_id
        )

        assert result is True

    def test_person_exists_by_both_ids_false(self, person_service, mock_session):
        """Test person exists by both Mayo IDs returns False."""
        login_id = "nonexistent"
        person_id = "nonexistent"
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        result = person_service.person_exists_by_mayo_ids(
            login_id=login_id,
            person_id=person_id
        )

        assert result is False

    def test_person_exists_by_neither_id(self, person_service, mock_session):
        """Test person exists with neither ID provided returns False."""
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query

        result = person_service.person_exists_by_mayo_ids()

        assert result is False
        mock_session.query.assert_called_once_with(Person)
        # No filters should be called since no IDs were provided
        mock_query.filter.assert_not_called()

    def test_person_exists_login_id_found_person_id_not_checked(self, person_service, mock_session, sample_person):
        """Test person exists when login ID is found, person ID is not checked."""
        login_id = "jdoe"
        person_id = "12345"
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_person

        result = person_service.person_exists_by_mayo_ids(
            login_id=login_id,
            person_id=person_id
        )

        assert result is True
        # Should only check login ID since it was found
        assert mock_query.filter.call_count == 1