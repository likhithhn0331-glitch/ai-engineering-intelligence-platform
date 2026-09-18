from typing import Literal

from fastapi import APIRouter, Depends, Query, status

from src.exceptions.document_exceptions import DocumentNotFoundError, InvalidDocumentError
from src.models.pydantic_model import DocumentCreate, DocumentResponse
from src.repositories.document_repository import DocumentRepository
from src.services.document_service import DocumentService

router = APIRouter()

repository = DocumentRepository()
service = DocumentService(repository)


def get_document_service() -> DocumentService:
    return service


@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(document: DocumentCreate, service: DocumentService = Depends(get_document_service)):
    created_document = service.create_document(document.model_dump())
    return DocumentResponse(
        id=created_document.id,
        name=created_document.name,
        document_type=created_document.document_type,
        version=created_document.version,
        status=created_document.status,
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, service: DocumentService = Depends(get_document_service)):
    document = service.get_document(document_id)
    return DocumentResponse(
        id=document.id,
        name=document.name,
        document_type=document.document_type,
        version=document.version,
        status=document.status,
    )


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    document_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    name_contains: str | None = Query(default=None, min_length=1),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: Literal["id", "name", "document_type", "version", "status", "created_at"] = "created_at",
    sort_order: Literal["asc", "desc"] = "asc",
    service: DocumentService = Depends(get_document_service),
):
    documents = service.list_documents(
        document_type=document_type,
        status=status_filter,
        name_contains=name_contains,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return [
        DocumentResponse(
            id=document.id,
            name=document.name,
            document_type=document.document_type,
            version=document.version,
            status=document.status,
        )
        for document in documents
    ]


@router.put("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    updated_data: dict,
    service: DocumentService = Depends(get_document_service),
):
    document = service.update_document(document_id, updated_data)
    return DocumentResponse(
        id=document.id,
        name=document.name,
        document_type=document.document_type,
        version=document.version,
        status=document.status,
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str, service: DocumentService = Depends(get_document_service)):
    service.delete_document(document_id)
    return None
