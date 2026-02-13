from app.core.database import Base
from sqlalchemy import (
    Column, Integer, String, Enum, DateTime,
    Boolean, ForeignKey, JSON, Float, func , UniqueConstraint
)
from sqlalchemy.orm import relationship


class LearningResource(Base):
    __tablename__ = "learning_resource"

    id = Column(String, primary_key=True, index=True, nullable=False)

    resource_type = Column(String, index=True, nullable=False)  # video, article, topic
    platform = Column(String, index=True, nullable=False)        # youtube, custom

    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)

    total_duration_seconds = Column(Integer, nullable=True)
    total_chapters = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationship
    chapters = relationship("LearningResourceChapter", back_populates="resource")


class LearningResourceChapter(Base):
    __tablename__ = "learning_resource_chapter"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    learning_resource_id = Column(
        String, ForeignKey("learning_resource.id", ondelete="CASCADE"), nullable=False
    )

    index = Column(Integer, index=True, nullable=False)
    title = Column(String, nullable=False)
    time = Column(String, nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)

    transcript = Column(String, nullable=True)

    quiz_generated = Column(Boolean, default=False)
    quiz_data = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    resource = relationship("LearningResource", back_populates="chapters")
    __table_args__ = (
        # ✅ UNIQUE combination
        UniqueConstraint('learning_resource_id', 'index', name='uq_lr_index'),
    )


class UserLearningProgress(Base):
    __tablename__ = "user_learning_progress"

    id = Column(Integer, primary_key=True, index=True,nullable=False, autoincrement=True)

    user_id = Column(Integer, index=True, nullable=False)  # FK to user table in your auth system
    learning_resource_id = Column(
        String, ForeignKey("learning_resource.id", ondelete="CASCADE"), nullable=False
    )

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    completed_chapters = Column(Integer, default=0)
    total_score = Column(Float, default=0.0)

    is_completed = Column(Boolean, default=False)
    daily_bite_enabled = Column(Boolean, default=False)
    job_id = Column(String, nullable=True)
    resource = relationship("LearningResource")
    chapters_progress = relationship("UserChapterProgress", back_populates="user_progress")
    __table_args__ = (
        # ✅ UNIQUE combination
        UniqueConstraint('learning_resource_id', 'user_id', name='uq_lr_user'),
    )


class UserChapterProgress(Base):
    __tablename__ = "user_chapter_progress"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    user_learning_progress_id = Column(
        Integer,
        ForeignKey("user_learning_progress.id", ondelete="CASCADE"),
        nullable=False
    )

    learning_resource_chapter_id = Column(
        Integer,
        ForeignKey("learning_resource_chapter.id", ondelete="CASCADE"),
        nullable=False
    )

    watched = Column(Boolean, default=False)
    quiz_attempted = Column(Boolean, default=False)

    score_percent = Column(Float, nullable=True)
    is_passed = Column(Boolean, default=False)

    attempts_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)

    user_progress = relationship("UserLearningProgress", back_populates="chapters_progress")
    __table_args__ = (
        # ✅ UNIQUE combination
        UniqueConstraint('user_learning_progress_id', 'learning_resource_chapter_id', name='uq_ulp_lrc'),
    )
