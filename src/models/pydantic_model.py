from pydantic import BaseModel


class DocumentCreate(BaseModel):
    name: str
    document_type: str
    version: str


class DocumentResponse(BaseModel):
    id: str
    name: str
    document_type: str
    version: str
    status: str
