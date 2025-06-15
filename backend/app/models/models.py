from typing import Optional, List, Dict
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel, Field as PydanticField, computed_field
from sqlalchemy import Column, DateTime, Integer, ForeignKey, Date, String, Boolean



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



class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    oauth_provider: Optional[str] = Field(default=None)
    oauth_sub: Optional[str] = Field(default=None)
    email: str = Field(unique=True, index=True)
    name: str = Field(unique=True, index=True)
    is_admin: bool = Field(default=False)
    password_hash: Optional[str] = Field(default=None)
    is_local: bool = Field(default=False)
    last_login: Optional[datetime] = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=True
        )
    )
    last_logout: Optional[datetime] = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=True
        )
    )

    archives: List["Archive"] = Relationship(back_populates="uploader")

class Course(SQLModel, table=True):
    __tablename__ = "courses"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
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
    download_count: int = Field(default=0)
    
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
    deleted_at: Optional[datetime] = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=True
        )
    )

class Meme(SQLModel, table=True):
    __tablename__ = "memes"
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    language: str



class UserRead(BaseModel):
    id: int
    email: str
    name: str
    is_admin: bool
    is_local: bool
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    is_admin: bool = False

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None

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
    download_count: int = 0
    
    class Config:
        from_attributes = True

class CourseCreate(BaseModel):
    name: str
    category: CourseCategory

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[CourseCategory] = None

class CourseRead(BaseModel):
    id: int
    name: str
    category: CourseCategory

    class Config:
        from_attributes = True

class ArchiveUpdateCourse(BaseModel):
    course_id: Optional[int] = None
    course_name: Optional[str] = None
    course_category: Optional[CourseCategory] = None

 