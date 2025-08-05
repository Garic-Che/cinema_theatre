# src/schemas/notification.py
"""
Pydantic schemas for notification data structures.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserModel(BaseModel):
    """Schema for user data from AuthAPI."""
    
    login: str
    email: str
    modified: datetime
    roles: List[str] = Field(default_factory=list)


class BookmarkModel(BaseModel):
    """Schema for bookmark data from UGC_CRUD_API."""
    
    user_id: str
    content_id: str
    created_at: datetime


class LikeModel(BaseModel):
    """Schema for like data from UGC_CRUD_API."""
    
    user_id: str
    content_id: str
    rate: int


class CommentModel(BaseModel):
    """Schema for comment data from UGC_CRUD_API."""
    
    user_id: str
    content_id: str
    text: str


class PersonModel(BaseModel):
    """Schema for person data from TheatreAPI."""
    
    full_name: str
    roles: List[str] = Field(default_factory=list)


class GenreModel(BaseModel):
    """Schema for genre data from TheatreAPI."""
    
    name: str


class FilmModel(BaseModel):
    """Schema for film data from TheatreAPI."""
    
    id: str
    title: str
    imdb_rating: Optional[float] = None
    genres: List[GenreModel] = Field(default_factory=list)
    description: Optional[str] = None
    actors: List[PersonModel] = Field(default_factory=list)


class NotificationContent(BaseModel):
    """Schema for notification content data."""
    
    movies: List[FilmModel] = Field(default_factory=list)
    personal_message: str = ""
    user_stats: Dict[str, Any] = Field(default_factory=dict)


class NotificationRequest(BaseModel):
    """Schema for notification request to NotificationAPI."""
    
    to_id: str
    send_by: str = Field(..., pattern="^(email|websocket)$")
    content_key: str
    content_data: NotificationContent


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    
    success: bool
    message: str
    notification_id: Optional[str] = None