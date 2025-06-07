# models.py
from typing import Optional, List, Dict
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel, Field as PydanticField, computed_field
from sqlalchemy import Column, DateTime

# --- Enums for Course and Archive Structure ---

class CourseCategory(str, PyEnum):
    FRESHMAN = "freshman"
    SOPHOMORE = "sophomore"
    JUNIOR = "junior"
    SENIOR = "senior"
    GRADUATE = "graduate"
    INTERDISCIPLINARY = "interdisciplinary"

class ArchiveType(str, PyEnum):
    QUIZ = "quiz"
    MIDTERM = "midterm"
    FINAL = "final"
    OTHER = "other"

# --- SQLModel Table Definitions ---

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    oauth_provider: str
    oauth_sub: str
    email: str
    name: Optional[str] = None
    is_admin: bool = Field(default=False)

    archives: List["Archive"] = Relationship(back_populates="uploader")

class Course(SQLModel, table=True):
    __tablename__ = "courses"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    code: Optional[str] = Field(default=None, index=True)
    category: CourseCategory
    
    archives: List["Archive"] = Relationship(back_populates="course")

class Archive(SQLModel, table=True):
    __tablename__ = "archives"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    name: str
    academic_year: int
    archive_type: ArchiveType
    professor: str = Field(index=True)
    has_answers: bool = False
    
    object_name: str
    
    uploader_id: Optional[int] = Field(default=None, foreign_key="users.id")
    uploader: Optional["User"] = Relationship(back_populates="archives")
    
    course_id: int = Field(foreign_key="courses.id")
    course: "Course" = Relationship(back_populates="archives")
    
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False
        )
    )

class Meme(SQLModel, table=True):
    __tablename__ = "memes"
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    language: str

# --- Pydantic Schema for Request/Response ---

class UserRead(BaseModel):
    id: int
    oauth_provider: str
    oauth_sub: str
    email: str
    name: Optional[str] = None

    class Config:
        from_attributes = True

class UserRoles(BaseModel):
    user_id: int
    is_admin: bool = False
    
    class Config:
        from_attributes = True

class MemeRead(BaseModel):
    id: int
    content: str
    language: str

    class Config:
        from_attributes = True

class CourseInfo(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CoursesByCategory(BaseModel):
    freshman: List[CourseInfo] = []
    sophomore: List[CourseInfo] = []
    junior: List[CourseInfo] = []
    senior: List[CourseInfo] = []
    graduate: List[CourseInfo] = []
    interdisciplinary: List[CourseInfo] = []

    class Config:
        from_attributes = True

class ArchiveRead(BaseModel):
    id: int
    name: str
    academic_year: int
    archive_type: ArchiveType
    professor: str
    has_answers: bool
    created_at: datetime
    uploader_id: Optional[int] = None
    
    class Config:
        from_attributes = True
