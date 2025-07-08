from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class PersonBase(BaseModel):
    login_id: str = ""
    person_id: str = ""
    name_first: str = ""
    name_middle: str = ""
    name_last: str = ""


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    login_id: Optional[str] = None
    person_id: Optional[str] = None
    name_first: Optional[str] = None
    name_middle: Optional[str] = None
    name_last: Optional[str] = None


class Person(PersonBase):
    model_config = ConfigDict(from_attributes=True)

    # SQLite string ID (using Rails convention)
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
