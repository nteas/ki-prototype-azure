import datetime
import os
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class Log(BaseModel):
    user: str = Field(default="admin")
    change: str = "created"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(default=None)
    owner: str = Field(default="admin")
    classification: str = Field(default="public")
    logs: List[Log] = Field(default=[])
    frequency: Optional[str] = Field(default="monthly")
    flagged_pages: List[str] = Field(default=[])
    type: str = Field(default="pdf")
    file: Optional[str] = Field(default=None)
    file_pages: List[str] = Field(default=[])
    url: Optional[str] = Field(default=None)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    def __init__(self, **data):
        data.pop("_id", None)  # Remove _id from the data if it exists
        if data.get("title") is None and data.get("file") is not None:
            data["title"] = os.path.basename(data["file"])

        super().__init__(**data)

    class Config:
        extra = "allow"