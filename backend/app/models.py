from pydantic import BaseModel, Field

class RewriteRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    mode: str = Field("layman", pattern="^(layman)$")

class RewriteResponse(BaseModel):
    rewritten_text: str
    meta: dict | None = None

# --- Added By Shourya ---

from pydantic import Field
from typing import List, Optional

# Models for /upload
class UploadResponse(BaseModel):
    session_id: str = Field(..., description="Unique ID for this document session.")
    filename: str
    message: str = "File uploaded and text extracted successfully."

# Models for /map
class TimelineEvent(BaseModel):
    date_description: str
    event: str

class DocumentSection(BaseModel):
    title: str
    content_summary: str
    subsections: List['DocumentSection'] = []

DocumentSection.model_rebuild()

class MapResponse(BaseModel):
    structure: List[DocumentSection]
    timeline: List[TimelineEvent]

# Models for /ask
class AskRequest(BaseModel):
    contract_text: str  # We will send the text directly
    question: str

class AskResponse(BaseModel):
    answer: str
    references: List[str] = Field([], description="Clause references or text excerpts used for the answer.")

###################################################################    