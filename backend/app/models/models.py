from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, String, Text
from sqlmodel import Field, Relationship, SQLModel


class CourseCategory(str, PyEnum):
    FRESHMAN = "freshman"
    SOPHOMORE = "sophomore"
    JUNIOR = "junior"
    SENIOR = "senior"
    GRADUATE = "graduate"
    INTERDISCIPLINARY = "interdisciplinary"
    GENERAL = "general"


class ArchiveType(str, PyEnum):
    QUIZ = "quiz"
    MIDTERM = "midterm"
    FINAL = "final"
    OTHER = "other"


class NotificationSeverity(str, PyEnum):
    INFO = "info"
    DANGER = "danger"


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    oauth_provider: Optional[str] = Field(default=None)
    oauth_sub: Optional[str] = Field(default=None)
    email: str = Field(unique=True, index=True)
    name: str = Field(unique=True, index=True)
    nickname: Optional[str] = Field(default=None, index=True)
    is_admin: bool = Field(default=False)
    password_hash: Optional[str] = Field(default=None)
    is_local: bool = Field(default=False)
    gemini_api_key: Optional[str] = Field(default=None)
    deleted_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    last_login: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    last_logout: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    archives: List["Archive"] = Relationship(back_populates="uploader")


class Course(SQLModel, table=True):
    __tablename__ = "courses"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    category: CourseCategory
    deleted_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )

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
            nullable=False,
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        )
    )
    deleted_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class ArchiveDiscussionMessage(SQLModel, table=True):
    __tablename__ = "archive_discussion_messages"
    id: Optional[int] = Field(default=None, primary_key=True)
    archive_id: int = Field(foreign_key="archives.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    content: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        )
    )
    deleted_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class Meme(SQLModel, table=True):
    __tablename__ = "memes"
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    language: str


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(sa_column=Column(String(150), nullable=False))
    body: str = Field(sa_column=Column(Text, nullable=False))
    severity: NotificationSeverity = Field(default=NotificationSeverity.INFO)
    is_active: bool = Field(default=True)
    deleted_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    starts_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    ends_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        )
    )


class UserRead(BaseModel):
    id: int
    email: str
    name: str
    nickname: Optional[str] = None
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


class UserNicknameUpdate(BaseModel):
    nickname: str


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


class NotificationBase(BaseModel):
    title: str
    body: str
    severity: NotificationSeverity = NotificationSeverity.INFO
    is_active: bool = True
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    severity: Optional[NotificationSeverity] = None
    is_active: Optional[bool] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class NotificationRead(NotificationBase):
    id: int
    created_at: datetime
    updated_at: datetime

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
    general: List[CourseInfo] = []

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


class ArchiveDiscussionMessageRead(BaseModel):
    id: int
    archive_id: int
    user_id: int
    user_name: str
    content: str
    created_at: datetime

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


# AI Exam related models


class GenerateExamRequest(BaseModel):
    archive_ids: List[int]
    prompt: Optional[str] = None
    temperature: Optional[float] = 0.7


class TaskSubmitResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # pending, in_progress, complete, failed, not_found
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class GenerateExamResponse(BaseModel):
    success: bool
    generated_content: str
    archives_used: List[dict]


# API Key related models


class ApiKeyUpdate(BaseModel):
    gemini_api_key: Optional[str] = None


class ApiKeyResponse(BaseModel):
    has_api_key: bool
    api_key_masked: Optional[str] = None
