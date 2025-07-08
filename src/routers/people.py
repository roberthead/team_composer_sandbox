from __future__ import annotations
from typing import List
# UUID import removed - using string IDs for SQLite

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database.connection import get_db_session
from src.services.person_service import PersonService
from src.schemas.person import Person, PersonCreate, PersonUpdate


router = APIRouter(prefix="/people", tags=["people"])


def get_person_service(db: Session = Depends(get_db_session)) -> PersonService:
    """Dependency to get PersonService instance."""
    return PersonService(db)


@router.post("/", response_model=Person, status_code=status.HTTP_201_CREATED)
def create_person(
    person_data: PersonCreate,
    service: PersonService = Depends(get_person_service)
) -> Person:
    """
    Create a new person record.

    - **login_id**: Mayo Clinic login ID (must be unique)
    - **person_id**: Mayo Clinic person ID (must be unique)
    - **name_first**: First name
    - **name_middle**: Middle name (optional)
    - **name_last**: Last name
    """
    try:
        # Check for existing Mayo IDs
        if person_data.login_id and service.get_person_by_mayo_login_id(person_data.login_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Person with login_id '{person_data.login_id}' already exists"
            )

        if person_data.person_id and service.get_person_by_mayo_person_id(person_data.person_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Person with person_id '{person_data.person_id}' already exists"
            )

        return service.create_person(person_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[Person])
def get_people(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    name: str = Query(None, description="Search by name (first, middle, or last)"),
    service: PersonService = Depends(get_person_service)
) -> List[Person]:
    """
    Get a list of people with optional filtering and pagination.

    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (1-1000)
    - **name**: Optional name search (searches first, middle, and last names)
    """
    if name:
        return service.search_people_by_name(name, skip=skip, limit=limit)
    return service.get_people(skip=skip, limit=limit)


@router.get("/{person_id}", response_model=Person)
def get_person(
    person_id: str,
    service: PersonService = Depends(get_person_service)
) -> Person:
    """
    Get a specific person by their ID.

    - **person_id**: ID of the person to retrieve
    """
    person = service.get_person_by_id(person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with id {person_id} not found"
        )
    return person


@router.put("/{person_id}", response_model=Person)
def update_person(
    person_id: str,
    person_update: PersonUpdate,
    service: PersonService = Depends(get_person_service)
) -> Person:
    """
    Update a person's information.

    - **person_id**: ID of the person to update
    - Only provided fields will be updated
    - Mayo IDs must remain unique across all persons
    """
    # Check if person exists
    existing_person = service.get_person_by_id(person_id)
    if not existing_person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with id {person_id} not found"
        )

    try:
        # Check for Mayo ID conflicts with other people
        update_data = person_update.model_dump(exclude_none=True)

        if "login_id" in update_data:
            existing_with_login = service.get_person_by_mayo_login_id(update_data["login_id"])
            if existing_with_login and existing_with_login.id != person_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Person with login_id '{update_data['login_id']}' already exists"
                )

        if "person_id" in update_data:
            existing_with_person_id = service.get_person_by_mayo_person_id(update_data["person_id"])
            if existing_with_person_id and existing_with_person_id.id != person_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Person with person_id '{update_data['person_id']}' already exists"
                )

        updated_person = service.update_person(person_id, person_update)
        return updated_person
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_person(
    person_id: str,
    service: PersonService = Depends(get_person_service)
):
    """
    Delete a person record.

    - **person_id**: ID of the person to delete
    """
    success = service.delete_person(person_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with id {person_id} not found"
        )


@router.get("/mayo-login/{login_id}", response_model=Person)
def get_person_by_mayo_login_id(
    login_id: str,
    service: PersonService = Depends(get_person_service)
) -> Person:
    """
    Get a person by their Mayo login ID.

    - **login_id**: Mayo Clinic login ID to search for
    """
    person = service.get_person_by_mayo_login_id(login_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with login_id '{login_id}' not found"
        )
    return person


@router.get("/mayo-person/{person_id}", response_model=Person)
def get_person_by_mayo_person_id(
    person_id: str,
    service: PersonService = Depends(get_person_service)
) -> Person:
    """
    Get a person by their Mayo person ID.

    - **person_id**: Mayo Clinic person ID to search for
    """
    person = service.get_person_by_mayo_person_id(person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with person_id '{person_id}' not found"
        )
    return person


@router.get("/stats/count", response_model=dict)
def get_people_count(
    service: PersonService = Depends(get_person_service)
) -> dict:
    """
    Get the total count of people in the database.

    Returns the total number of person records.
    """
    count = service.count_people()
    return {"total_people": count}