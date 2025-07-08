from __future__ import annotations
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.person import Person
from src.schemas.person import PersonCreate, PersonUpdate


class PersonService:
    """Service layer for Person CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_person(self, person_data: PersonCreate) -> Person:
        """Create a new person record."""
        db_person = Person(**person_data.model_dump())

        try:
            self.db.add(db_person)
            self.db.commit()
            self.db.refresh(db_person)
            return db_person
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Person creation failed: {str(e)}")

    def get_person_by_id(self, person_id: str) -> Optional[Person]:
        """Get a person by their ID."""
        return self.db.query(Person).filter(Person.id == person_id).first()

    def get_person_by_mayo_login_id(self, login_id: str) -> Optional[Person]:
        """Get a person by their Mayo login ID."""
        return self.db.query(Person).filter(Person.login_id == login_id).first()

    def get_person_by_mayo_person_id(self, person_id: str) -> Optional[Person]:
        """Get a person by their Mayo person ID."""
        return self.db.query(Person).filter(Person.person_id == person_id).first()

    def get_people(self, skip: int = 0, limit: int = 100) -> List[Person]:
        """Get a list of people with pagination."""
        return self.db.query(Person).offset(skip).limit(limit).all()

    def search_people_by_name(self, name_query: str, skip: int = 0, limit: int = 100) -> List[Person]:
        """Search people by name (first, middle, or last)."""
        query = self.db.query(Person).filter(
            (Person.name_first.ilike(f"%{name_query}%")) |
            (Person.name_middle.ilike(f"%{name_query}%")) |
            (Person.name_last.ilike(f"%{name_query}%"))
        )
        return query.offset(skip).limit(limit).all()

    def update_person(self, person_id: str, person_update: PersonUpdate) -> Optional[Person]:
        """Update a person record."""
        db_person = self.get_person_by_id(person_id)
        if not db_person:
            return None

        # Get only the fields that were provided (exclude None values)
        update_data = person_update.model_dump(exclude_none=True)

        # Update the person with new values
        for field, value in update_data.items():
            setattr(db_person, field, value)

        try:
            self.db.commit()
            self.db.refresh(db_person)
            return db_person
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Person update failed: {str(e)}")

    def delete_person(self, person_id: str) -> bool:
        """Delete a person record."""
        db_person = self.get_person_by_id(person_id)
        if not db_person:
            return False

        self.db.delete(db_person)
        self.db.commit()
        return True

    def count_people(self) -> int:
        """Get the total count of people."""
        return self.db.query(Person).count()

    def person_exists_by_mayo_ids(self, login_id: str = None, person_id: str = None) -> bool:
        """Check if a person exists with the given Mayo IDs."""
        query = self.db.query(Person)

        if login_id:
            if query.filter(Person.login_id == login_id).first():
                return True

        if person_id:
            if query.filter(Person.person_id == person_id).first():
                return True

        return False