# Task 2 — POST /documents Flow (Detailed Explanation)

```text
POST /documents
    |
    v
Pydantic validation
    |
    v
API layer
    |
    v
DocumentService
    |
    v
DocumentRepository
    |
    v
In-memory store
    |
    v
DocumentResponse
    |
    v
HTTP response
```

Detailed flow:

1. POST /documents request arrives from the HTTP client.
   - The client sends JSON payload such as: {"name":"engine-requirement","document_type":"requirement","version":"1.0"}
   - FastAPI routes the request to the `create_document` endpoint defined in `src/api/document_routes.py`.

2. Pydantic validation runs first.
   - The payload is validated against `DocumentCreate` in `src/models/pydantic_model.py`.
   - If required fields are missing or types are invalid, FastAPI raises `RequestValidationError` and responds with HTTP 422.

3. API layer processes the validated payload.
   - The route calls `service.create_document(document.model_dump())`.
   - This keeps HTTP-specific concerns in the API layer and defers business logic to the service layer.

4. DocumentService enforces business rules.
   - It checks for empty names, unsupported document types, and duplicate names.
   - If invalid, it raises `InvalidDocumentError`, which the global exception handler converts into HTTP 400.
   - If valid, it creates the domain `Document` object and assigns a generated ID.

5. DocumentRepository saves the document.
   - The repository stores the `Document` in an in-memory dictionary using the document ID as the key.
   - This is the persistence layer in the current implementation.

6. In-memory storage confirms persistence.
   - The document is now available for future retrieval, update, or deletion operations.
   - Since this is in-memory storage, it is ephemeral and resets when the app restarts.

7. DocumentResponse is constructed.
   - The route converts the stored `Document` to the `DocumentResponse` model with `id`, `name`, `document_type`, `version`, and `status`.

8. HTTP response is returned.
   - The API responds with HTTP 201 Created and the JSON body of the newly created document.
   - Example response:
     {
       "id": "doc-001",
       "name": "engine-requirement",
       "document_type": "requirement",
       "version": "1.0",
       "status": "created"
     }

This flow demonstrates the layered design clearly: client -> validation -> API -> service -> repository -> storage -> response.
