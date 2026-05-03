from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime, UniqueConstraint, Index, Float, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    library = relationship("UserAnime", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")

class UserAnime(Base):
    __tablename__ = "user_animes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    anime_mal_id = Column(String, ForeignKey("animes.mal_id"), nullable=False, index=True)
    
    status = Column(String, default="plan_to_watch") # watching, completed, dropped, plan_to_watch
    is_favorite = Column(Boolean, default=False)
    progress_episode = Column(String, nullable=True) # Last watched episode
    # Resume time (seconds) for the last watched episode.
    progress_time = Column(Integer, nullable=True)
    last_watched_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    score = Column(Integer, nullable=True) # User's personal score
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="library")
    anime = relationship("Anime") # Unidirectional is fine for now, or backref

    __table_args__ = (
        UniqueConstraint('user_id', 'anime_mal_id', name='uq_user_anime'),
    )

class Anime(Base):
    __tablename__ = "animes"

    id = Column(Integer, primary_key=True, index=True)
    mal_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    
    # Enhanced Metadata
    genres = Column(Text, nullable=True) # JSON string
    score = Column(Float, nullable=True)
    status = Column(String, nullable=True)
    studios = Column(Text, nullable=True) # JSON string
    type = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    season = Column(String, nullable=True)
    rating = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    trailer_url = Column(String, nullable=True)
    rank = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    episodes = relationship("Episode", back_populates="anime", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="anime", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    anime_mal_id = Column(String, ForeignKey("animes.mal_id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Linked to User
    
    user_name = Column(String, default="Anonymous") # Fallback if user_id is null or just cache
    text = Column(String, nullable=False)
    likes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    anime = relationship("Anime", back_populates="comments")
    user = relationship("User", back_populates="comments")

    __table_args__ = (
        Index('idx_comment_anime_created', 'anime_mal_id', 'created_at'),
    )

class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    anime_mal_id = Column(String, ForeignKey("animes.mal_id"), nullable=False, index=True)
    
    episode_number = Column(String, index=True)
    label = Column(String)
    quality = Column(String, nullable=True)
    
    file_id = Column(String, index=True, nullable=False)
    file_unique_id = Column(String, nullable=True)
    
    file_size = Column(BigInteger, default=0)
    mime_type = Column(String, default="video/mp4")
    
    views = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    
    anime = relationship("Anime", back_populates="episodes")

    __table_args__ = (
        UniqueConstraint('anime_mal_id', 'episode_number', 'quality', name='uq_anime_ep_quality'),
    )
