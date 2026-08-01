from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import validates, Session
from .database import Base
from typing import List, Optional, Dict, Any
import re
import unicodedata


def generate_slug(title: str, db_session: Optional[Session] = None, model_class=None) -> str:
    """
    Generate a URL-safe slug from a title.

    Args:
        title: The title to convert to a slug
        db_session: Optional database session to check for uniqueness
        model_class: The model class to check against (e.g., News)

    Returns:
        A URL-safe slug string
    """
    if not title:
        return ""

    # Convert to lowercase
    slug = title.lower()

    # Remove accents and special characters
    slug = unicodedata.normalize('NFKD', slug)
    slug = slug.encode('ascii', 'ignore').decode('ascii')

    # Drop apostrophes/quotes so possessives collapse cleanly
    # ("australia's role" -> "australias-role", not "australia-s-role").
    slug = re.sub(r"['\"`]", '', slug)

    # Replace remaining spaces and special characters with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    # Remove consecutive hyphens
    slug = re.sub(r'-+', '-', slug)

    # Limit length to 250 characters
    slug = slug[:250]

    # Handle uniqueness if db_session provided
    if db_session and model_class:
        original_slug = slug
        counter = 2
        while db_session.query(model_class).filter(model_class.slug == slug).first():
            slug = f"{original_slug}-{counter}"
            counter += 1

    return slug


class News(Base):
    """
    News model representing articles in the database.
    """
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    summary = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True, default=list)
    _image_url_legacy = Column('image_url', String(500), nullable=True)  # Deprecated - kept for backward compatibility
    image_data = Column(LargeBinary, nullable=True)  # Store actual image binary data
    image_filename = Column(String(255), nullable=True)  # Store original filename
    image_mimetype = Column(String(100), nullable=True)  # Store MIME type (image/jpeg, etc.)
    published = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    author_id = Column(Integer, nullable=True)  # Reference to user who created the news
    slug = Column(String(300), unique=True, nullable=True)  # URL-friendly version of title

    @property
    def image_url(self) -> Optional[str]:
        """Computed property that returns the correct image URL"""
        if self.image_data:
            return f"/news/image/{self.id}"
        elif self._image_url_legacy:  # Backward compatibility with old file-based images
            return self._image_url_legacy
        return None

    @validates('tags')
    def validate_tags(self, key, tags):
        """Ensure tags is always a list"""
        if tags is None:
            return []
        if isinstance(tags, str):
            # If it's a string, convert to list
            return [tags.strip()] if tags.strip() else []
        if isinstance(tags, list):
            return tags
        return []

    def _get_tags(self):
        """Property to ensure tags is always returned as a list"""
        tags_value = object.__getattribute__(self, '_sa_instance_state').dict.get('tags')
        if tags_value is None:
            return []
        if isinstance(tags_value, str):
            return [tags_value.strip()] if tags_value.strip() else []
        if isinstance(tags_value, list):
            return tags_value
        return []

    def generate_slug_from_title(self, db_session: Optional[Session] = None):
        """Generate and set slug from title if slug is not already set"""
        if not self.slug and self.title:
            self.slug = generate_slug(self.title, db_session, News)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        # Ensure tags is always a list
        tags_value = self.tags
        if isinstance(tags_value, str):
            tags_value = [tags_value.strip()] if tags_value.strip() else []
        elif tags_value is None:
            tags_value = []

        # Generate image URL if image data exists
        image_url = None
        if self.image_data:
            image_url = f"/news/image/{self.id}"
        elif self.image_url:  # Backward compatibility
            image_url = self.image_url

        return {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'content': self.content,
            'tags': tags_value,
            'image_url': image_url,
            'published': self.published,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'author_id': self.author_id,
            'slug': self.slug
        }
        
    def __repr__(self) -> str:
        return f"<News(id={self.id}, title='{self.title[:20]}...', published={self.published})>"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create a News instance from a dictionary"""
        return cls(
            title=data.get('title'),
            summary=data.get('summary'),
            content=data.get('content'),
            tags=data.get('tags', []),
            image_url=data.get('image_url'),
            published=data.get('published', False),
            author_id=data.get('author_id'),
            slug=data.get('slug')
        )


class Job(Base):
    """
    Job listing — sourced from a free jobs API on a schedule and/or added
    manually via the admin dashboard. Table auto-creates on startup via
    Base.metadata.create_all (see app/main.py); no migration needed.
    """
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    remote = Column(Boolean, default=False, index=True)
    job_type = Column(String(100), nullable=True)      # Full-time, Contract, …
    category = Column(String(100), nullable=True, index=True)  # software-dev, data, …
    tags = Column(JSON, nullable=True, default=list)
    description = Column(Text, nullable=True)           # HTML/markdown from source
    apply_url = Column(String(1000), nullable=False)
    company_logo = Column(String(1000), nullable=True)
    salary = Column(String(255), nullable=True)
    source = Column(String(100), nullable=True, index=True)     # 'remotive' | 'manual'
    source_id = Column(String(150), nullable=True, index=True)  # dedupe key within a source
    published = Column(Boolean, default=True, index=True)
    pinned = Column(Boolean, default=False, index=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    slug = Column(String(350), unique=True, nullable=True)

    @validates('tags')
    def validate_tags(self, key, tags):
        if tags is None:
            return []
        if isinstance(tags, str):
            return [tags.strip()] if tags.strip() else []
        if isinstance(tags, list):
            return tags
        return []

    def generate_slug_from_title(self, db_session: Optional[Session] = None):
        if not self.slug and self.title:
            base = f"{self.title} at {self.company}" if self.company else self.title
            self.slug = generate_slug(base, db_session, Job)

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title='{self.title[:20]}...', company='{self.company}')>"


class Contact(Base):
    """
    Contact model for storing contact form submissions.
    """
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read = Column(Boolean, default=False, index=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'subject': self.subject,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read': self.read
        }

    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, name='{self.name}', email='{self.email}')>"
