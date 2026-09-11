# AI Engineering Intelligence Platform

AI Engineering Change and Test Intelligence Platform.

## Architecture

The application follows a layered architecture for document management:

HTTP Client
↓
FastAPI Router
↓
DocumentService
↓
DocumentRepository
↓
In-Memory Store

This flow is implemented for the document endpoints:

POST /documents
↓
API Layer
↓
Service Layer
↓
Repository Layer
↓
Storage

## Project Structure

- `src/main.py` – FastAPI app entry point and root/health routes
- `src/api/document_routes.py` – HTTP endpoints for document operations
- `src/services/document_service.py` – Business logic, validation, and orchestration
- `src/repositories/document_repository.py` – In-memory persistence layer
- `src/models/pydantic_model.py` – Request/response schemas
- `src/data_classes/document_class.py` – Document domain model
- `src/exceptions/document_exceptions.py` – Custom exceptions

## Document API

### Create document

Request:

```json
{
  "name": "engine-requirement",
  "document_type": "requirement",
  "version": "1.0"
}
```

Response:

```json
{
  "id": "doc-001",
  "name": "engine-requirement",
  "document_type": "requirement",
  "version": "1.0",
  "status": "created"
}
```

### Supported document types

- `requirement`
- `design`
- `test`

### Endpoints

- `GET /` – app status
- `GET /health` – health check
- `POST /documents` – create a document
- `GET /documents` – list all documents
- `GET /documents/{document_id}` – fetch a document
- `PUT /documents/{document_id}` – update a document
- `DELETE /documents/{document_id}` – delete a document

## Notes

- The repository layer currently uses an in-memory dictionary for persistence.
- This is a foundational implementation for the platform architecture and can be extended to a database-backed repository later.
