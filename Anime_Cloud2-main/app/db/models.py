from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime, UniqueConstraint, Index, Float, Text, Boolean, Computed, JSON
from sqlalchemy.dialects.postgresql import TSVECTOR, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional
from datetime import datetime, timezone
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    library: Mapped[List["UserAnime"]] = relationship("UserAnime", back_populates="user", cascade="all, delete-orphan")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="user", cascade="all, delete-orphan")

class UserAnime(Base):
    __tablename__ = "user_animes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    anime_mal_id: Mapped[str] = mapped_column(String, ForeignKey("animes.mal_id"), nullable=False, index=True)
    
    status: Mapped[str] = mapped_column(String, default="plan_to_watch") # watching, completed, dropped, plan_to_watch
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    progress_episode: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Last watched episode
    # Resume time (seconds) for the last watched episode.
    progress_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_watched_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # User's personal score
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="library")
    anime: Mapped["Anime"] = relationship("Anime") # Unidirectional is fine for now, or backref

    __table_args__ = (
        UniqueConstraint('user_id', 'anime_mal_id', name='uq_user_anime'),
    )

class Anime(Base):
    __tablename__ = "animes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    mal_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Enhanced Metadata
    genres: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    studios: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    season: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rating: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    duration: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    trailer_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # PostgreSQL Full-Text Search Vector
    search_vector = Column(TSVECTOR().with_variant(Text, "sqlite"))

    episodes: Mapped[List["Episode"]] = relationship("Episode", back_populates="anime", cascade="all, delete-orphan")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="anime", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    anime_mal_id: Mapped[str] = mapped_column(String, ForeignKey("animes.mal_id"), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True) # Linked to User
    
    user_name: Mapped[str] = mapped_column(String, default="Anonymous") # Fallback if user_id is null or just cache
    text: Mapped[str] = mapped_column(String, nullable=False)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    anime: Mapped["Anime"] = relationship("Anime", back_populates="comments")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="comments")

    __table_args__ = (
        Index('idx_comment_anime_created', 'anime_mal_id', 'created_at'),
    )

class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    anime_mal_id: Mapped[str] = mapped_column(String, ForeignKey("animes.mal_id"), nullable=False, index=True)

    episode_number: Mapped[str] = mapped_column(String, index=True)
    label: Mapped[str] = mapped_column(String)
    quality: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    file_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    file_unique_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    mime_type: Mapped[str] = mapped_column(String, default="video/mp4")
    
    chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    views: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    anime: Mapped["Anime"] = relationship("Anime", back_populates="episodes")

    __table_args__ = (
        UniqueConstraint('anime_mal_id', 'episode_number', 'quality', name='uq_anime_ep_quality'),
    )
