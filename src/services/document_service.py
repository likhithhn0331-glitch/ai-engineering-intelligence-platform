from src.data_classes.document_class import Document
from src.exceptions.document_exceptions import InvalidDocumentError, DocumentNotFoundError


class DocumentService:
    def __init__(self, document_repository):
        self.document_repository = document_repository

    def create_document(self, document_data):
        valid_document_types = ["requirement", "design", "test"]
        name = document_data.get("name")
        document_type = document_data.get("document_type")
        version = document_data.get("version")

        if not name:
            raise InvalidDocumentError("Document name is required.")

        if document_type not in valid_document_types:
            raise InvalidDocumentError(
                f"Invalid document type '{document_type}'. Valid types are: {valid_document_types}."
            )

        existing_documents = self.document_repository.list_documents()
        for existing_doc in existing_documents:
            if existing_doc.name == name:
                raise InvalidDocumentError(f"Document with name '{name}' already exists.")

        if not document_data.get("id"):
            document_id = f"doc-{len(existing_documents) + 1:03d}"
        else:
            document_id = document_data.get("id")

        document = Document(
            id_=document_id,
            name=name,
            document_type=document_type,
            version=version,
            status=document_data.get("status", "created"),
        )
        return self.document_repository.create_document(document)

    def get_document(self, document_id):
        document = self.document_repository.get_document(document_id)
        if not document:
            raise DocumentNotFoundError(document_id)
        return document

    def update_document(self, document_id, updated_data):
        self.get_document(document_id)
        updated_document = self.document_repository.update_document(document_id, updated_data)
        if updated_document is None:
            raise DocumentNotFoundError(document_id)
        return updated_document

    def delete_document(self, document_id):
        self.get_document(document_id)
        deleted = self.document_repository.delete_document(document_id)
        if not deleted:
            raise DocumentNotFoundError(document_id)
        return True

    def list_documents(self):
        return self.document_repository.list_documents()
