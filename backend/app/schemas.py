from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime
from typing import Optional, List, Any


class NewsBase(BaseModel):
    title: str
    summary: str
    content: str
    tags: Optional[List[str]] = None
    published: bool = False

    @field_validator('tags', mode='before')
    @classmethod
    def validate_tags(cls, v):
        """Ensure tags is always a list"""
        if v is None:
            return []
        if isinstance(v, str):
            # If it's a string, convert to list
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            return v
        return []


class NewsCreate(NewsBase):
    pass


class NewsUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    published: Optional[bool] = None

    @field_validator('tags', mode='before')
    @classmethod
    def validate_tags(cls, v):
        """Ensure tags is always a list"""
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            return v
        return []


class NewsResponse(NewsBase):
    id: int
    image_url: Optional[str] = None
    created_at: datetime
    slug: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def compute_image_url(cls, data):
        """Compute image_url from image_data if available"""
        if isinstance(data, dict):
            return data
        # If it's a model instance, convert to dict
        if hasattr(data, '__dict__'):
            # Get the model's attributes
            result = {}
            for key in ['id', 'title', 'summary', 'content', 'tags', 'published', 'created_at', 'updated_at', 'author_id', 'slug']:
                if hasattr(data, key):
                    result[key] = getattr(data, key)

            # Compute image_url
            if hasattr(data, 'image_data') and data.image_data:
                result['image_url'] = f"/news/image/{data.id}"
            elif hasattr(data, '_image_url_legacy') and data._image_url_legacy:
                result['image_url'] = data._image_url_legacy
            else:
                result['image_url'] = None

            return result
        return data

    class Config:
        from_attributes = True


class NewsListResponse(BaseModel):
    id: int
    title: str
    summary: str
    tags: Optional[List[str]] = None
    image_url: Optional[str] = None
    published: bool
    created_at: datetime
    slug: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def compute_image_url(cls, data):
        """
        Compute image_url without touching image_data.

        The list query uses load_only() to defer the image_data binary
        blob (can be 50-300 KB per row). We detect image presence using
        image_filename instead, which is always loaded.
        """
        if isinstance(data, dict):
            return data
        if hasattr(data, '__dict__'):
            result = {}
            for key in ['id', 'title', 'summary', 'tags', 'published', 'created_at', 'slug']:
                if hasattr(data, key):
                    result[key] = getattr(data, key)

            # Use image_filename (lightweight text) to detect whether an
            # image was stored — avoids lazy-loading the binary blob.
            if getattr(data, 'image_filename', None):
                result['image_url'] = f"/news/image/{data.id}"
            elif getattr(data, '_image_url_legacy', None):
                result['image_url'] = data._image_url_legacy
            else:
                result['image_url'] = None

            return result
        return data

    @field_validator('tags', mode='before')
    @classmethod
    def validate_tags(cls, v):
        """Ensure tags is always a list"""
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            return v
        return []

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ContactCreate(BaseModel):
    name: str
    email: str
    subject: str
    message: str


class ContactResponse(BaseModel):
    id: int
    name: str
    email: str
    subject: str
    message: str
    created_at: datetime
    read: bool = False

    class Config:
        from_attributes = True
