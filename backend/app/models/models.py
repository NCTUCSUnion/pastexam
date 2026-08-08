from datetime import UTC, datetime
from enum import Enum as PyEnum
from typing import Optional

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
    id: int | None = Field(default=None, primary_key=True)
    oauth_provider: str | None = Field(default=None)
    oauth_sub: str | None = Field(default=None)
    email: str = Field(unique=True, index=True)
    name: str = Field(unique=True, index=True)
    nickname: str | None = Field(default=None, index=True)
    is_admin: bool = Field(default=False)
    password_hash: str | None = Field(default=None)
    is_local: bool = Field(default=False)
    gemini_api_key: str | None = Field(default=None)
    deleted_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    last_login: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    last_logout: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    archives: list["Archive"] = Relationship(back_populates="uploader")


class Course(SQLModel, table=True):
    __tablename__ = "courses"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    category: CourseCategory
    deleted_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    archives: list["Archive"] = Relationship(back_populates="course")


class Archive(SQLModel, table=True):
    __tablename__ = "archives"
    id: int | None = Field(default=None, primary_key=True)

    name: str
    academic_year: int
    archive_type: ArchiveType
    professor: str = Field(index=True)
    has_answers: bool = False
    download_count: int = Field(default=0)

    object_name: str

    uploader_id: int | None = Field(default=None, foreign_key="users.id")
    uploader: Optional["User"] = Relationship(back_populates="archives")

    course_id: int = Field(foreign_key="courses.id")
    course: "Course" = Relationship(back_populates="archives")

    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(UTC),
            nullable=False,
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(UTC),
            nullable=False,
        )
    )
    deleted_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class ArchiveDiscussionMessage(SQLModel, table=True):
    __tablename__ = "archive_discussion_messages"
    id: int | None = Field(default=None, primary_key=True)
    archive_id: int = Field(foreign_key="archives.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    content: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(UTC),
            nullable=False,
        )
    )
    deleted_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class Meme(SQLModel, table=True):
    __tablename__ = "memes"
    id: int | None = Field(default=None, primary_key=True)
    content: str
    language: str


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(sa_column=Column(String(150), nullable=False))
    body: str = Field(sa_column=Column(Text, nullable=False))
    severity: NotificationSeverity = Field(default=NotificationSeverity.INFO)
    is_active: bool = Field(default=True)
    deleted_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    starts_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    ends_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(UTC),
            nullable=False,
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(UTC),
            nullable=False,
        )
    )


class UserRead(BaseModel):
    id: int
    email: str
    name: str
    nickname: str | None = None
    is_admin: bool
    is_local: bool
    last_login: datetime | None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    is_admin: bool = False


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None
    is_admin: bool | None = None


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
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    severity: NotificationSeverity | None = None
    is_active: bool | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


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
    freshman: list[CourseInfo] = []
    sophomore: list[CourseInfo] = []
    junior: list[CourseInfo] = []
    senior: list[CourseInfo] = []
    graduate: list[CourseInfo] = []
    interdisciplinary: list[CourseInfo] = []
    general: list[CourseInfo] = []

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
    uploader_id: int | None = None
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
    name: str | None = None
    category: CourseCategory | None = None


class CourseRead(BaseModel):
    id: int
    name: str
    category: CourseCategory

    class Config:
        from_attributes = True


class ArchiveUpdateCourse(BaseModel):
    course_id: int | None = None
    course_name: str | None = None
    course_category: CourseCategory | None = None


# AI Exam related models


class GenerateExamRequest(BaseModel):
    archive_ids: list[int]
    prompt: str | None = None
    temperature: float | None = 0.7


class TaskSubmitResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # pending, in_progress, complete, failed, not_found
    result: dict | None = None
    error: str | None = None
    created_at: str | None = None
    completed_at: str | None = None


class GenerateExamResponse(BaseModel):
    success: bool
    generated_content: str
    archives_used: list[dict]


# API Key related models


class ApiKeyUpdate(BaseModel):
    gemini_api_key: str | None = None


class ApiKeyResponse(BaseModel):
    has_api_key: bool
    api_key_masked: str | None = None
