from __future__ import annotations
from typing import Optional, Union
from datetime import datetime
import uuid as uuid_lib
import os

from sqlalchemy import String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Person(Base):
    __tablename__ = "people"

    # SQLite configuration for id field (using Rails convention)
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid_lib.uuid4())
    )
    login_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        server_default=""
    )
    person_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        server_default=""
    )
    name_first: Mapped[str] = mapped_column(String, server_default="")
    name_middle: Mapped[str] = mapped_column(String, server_default="")
    name_last: Mapped[str] = mapped_column(String, server_default="")

    # SQLite datetime configuration (using Rails convention)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    def name_full(self):
        parts = []
        if self.name_first:
            parts.append(self.name_first)
        if self.name_middle:
            parts.append(self.name_middle)
        if self.name_last:
            parts.append(self.name_last)
        return " ".join(parts)

    def identifiers(self):
        return ", ".join([
            str(self.id),
            self.login_id,
            self.person_id,
        ])

    def __repr__(self):
        return f"<Person(id={self.id}, name='{self.name_full()}', login_id='{self.login_id}')>"
