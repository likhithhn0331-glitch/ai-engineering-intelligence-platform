from src.data_classes.document_class import Document


class DocumentRepository:
    def __init__(self):
        self.documents = {}

    def create_document(self, document: Document):
        self.documents[document.id] = document
        return document

    def get_document(self, document_id):
        return self.documents.get(document_id)

    def delete_document(self, document_id):
        if document_id in self.documents:
            del self.documents[document_id]
            return True
        return False

    def list_documents(self):
        return list(self.documents.values())

    def update_document(self, document_id, updated_data):
        document = self.documents.get(document_id)
        if not document:
            return None
        for key, value in updated_data.items():
            if hasattr(document, key):
                setattr(document, key, value)
        return document

    def update(self, document_id, updated_data):
        return self.update_document(document_id, updated_data)
